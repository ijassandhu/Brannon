odoo.define('mtr_module.mtr_chatbot', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var _t = core._t;

    var MtrChatbot = AbstractAction.extend({
        template: 'mtr_module.MtrChatbot',
        events: {
            'click .o_mtr_chatbot_send': '_onSend',
            'keydown .o_mtr_chatbot_input_text': '_onKeydown',
            'click .o_mtr_chatbot_open_inventory': '_onOpenInventory',
            'click .o_mtr_chatbot_open_join': '_onOpenJoin',
            'click .o_mtr_chatbot_open_mtr': '_onOpenMtr',
            'click .o_mtr_chatbot_choose_branch': '_onChooseBranch',
            'click .o_mtr_chatbot_clear': '_onClear',
        },

        start: function () {
            this.$messages = this.$('.o_mtr_chatbot_messages');
            this._mode = this._getModeFromContext();
            this._plannerMode = this._mode === 'planner';
            this._stateKey = this._plannerMode ? 'mtr_spec_planner_state' : 'mtr_chatbot_state';
            this._autoMatched = false;
            this._restoring = true;
            this._specName = this._getSpecNameFromContext();
            this._specId = this._getSpecIdFromContext();
            this._branchId = this._getBranchIdFromContext();
            if (this._shouldResetStateFromContext()) {
                window.sessionStorage.removeItem(this._stateKey);
            }
            this._applyModeUi();
            if (!this._restoreState()) {
                this._appendMessage(
                    'assistant',
                    this._plannerMode
                        ? _t('Ask me to turn this spec into a filtering plan or explain any custom rule.')
                        : _t('Ask me about an MTR by batch number, grade, or chemical specs.')
                );
            }
            this._restoring = false;
            this._renderContext();
            if (this._plannerMode) {
                this._autoPlanFromContext();
                this._autoPlanFromLastSpec();
            } else {
                this._bootstrapMatchFlow();
            }
            return this._super.apply(this, arguments);
        },

        _onKeydown: function (ev) {
            if (ev.keyCode === 13 && !ev.shiftKey) {
                ev.preventDefault();
                this._onSend();
            }
        },

        _onSend: function () {
            var $input = this.$('.o_mtr_chatbot_input_text');
            var text = ($input.val() || '').trim();
            if (!text) {
                return;
            }
            $input.val('');
            this._appendMessage('user', text);
            this._setLoading(true);
            var debugLlm = window.location.search.indexOf('debug_llm=1') !== -1;

            // Build conversation history for Claude (last 20 messages, text only)
            var history = [];
            var state = this._getState() || [];
            var msgEntries = state.filter(function (e) { return e.type === 'message'; });
            // exclude the message we just appended (last entry)
            msgEntries = msgEntries.slice(0, msgEntries.length - 1).slice(-20);
            msgEntries.forEach(function (e) {
                history.push({ role: e.role, text: e.text });
            });

            var self = this;

            // Use fetch-based streaming for Claude responses
            if (!self._plannerMode) {
                self._sendStreaming(text, debugLlm, history);
                return;
            }

            rpc.query({
                route: '/mtr_module/spec_filter_plan',
                params: { spec_id: this._specId, message: text, debug_llm: debugLlm },
            }).then(function (response) {
                self._setLoading(false);
                if (response && response.error) {
                    self._appendMessage('assistant', response.error);
                    return;
                }
                if (response && response.debug_llm) {
                    self._appendMessage('assistant', 'LLM raw: ' + response.debug_llm);
                }
                if (response && response.answer) {
                    self._appendMessage('assistant', response.answer);
                } else {
                    self._appendMessage('assistant', _t('No filtering plan was returned.'));
                }
            }).guardedCatch(function () {
                self._setLoading(false);
                self._appendMessage('assistant', _t('Something went wrong. Please try again.'));
            });
        },

        _setLoading: function (isLoading) {
            this.$('.o_mtr_chatbot_send').prop('disabled', isLoading);
            this.$('.o_mtr_chatbot_loading').toggleClass('o_hidden', !isLoading);
        },

        // Fetch the response via JSON-RPC then typewrite it into the chat bubble
        _sendStreaming: function (text, debugLlm, history) {
            var self = this;
            var payload = JSON.stringify({
                jsonrpc: '2.0',
                method: 'call',
                id: Math.floor(Math.random() * 1e9),
                params: {
                    message: text,
                    debug_llm: debugLlm,
                    spec_id: this._specId,
                    branch_id: this._branchId,
                    history: history,
                },
            });

            fetch('/mtr_module/mtr_chatbot', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: payload,
            })
            .then(function (res) { return res.json(); })
            .then(function (json) {
                self._setLoading(false);
                var response = json.result || json;

                if (response && response.error) {
                    self._appendMessage('assistant', typeof response.error === 'string' ? response.error : JSON.stringify(response.error));
                    return;
                }
                if (response && response.need_branch && response.branches && response.branches.length) {
                    self._appendMessage('assistant', response.answer || _t('Please choose a branch to continue.'));
                    self._appendBranchChoices(response.branches);
                    return;
                }
                var answer = (response && response.answer) || '';
                if (!answer && !response.results) {
                    self._appendMessage('assistant', _t('No matching records found.'));
                    return;
                }
                if (answer) {
                    self._typewriteMessage(answer, function () {
                        if (response.results && response.results.length) {
                            self._appendResults(response.results);
                        }
                    });
                } else if (response.results && response.results.length) {
                    self._appendResults(response.results);
                }
            })
            .catch(function (err) {
                self._setLoading(false);
                self._appendMessage('assistant', _t('Error: ') + (err.message || _t('Something went wrong. Please try again.')));
            });
        },

        // Progressive typewriter reveal — creates the bubble then fills it character by character
        _typewriteMessage: function (text, onDone) {
            var self = this;
            var $msg = $('<div>', { class: 'o_mtr_chatbot_message o_mtr_chatbot_message_assistant o_typing' });
            this.$messages.append($msg);

            var chars = Array.from(text); // unicode-safe split
            var chunkSize = 5;            // chars per tick
            var delay = 10;               // ms between ticks
            var pos = 0;
            var accumulated = '';

            function tick() {
                var end = Math.min(pos + chunkSize, chars.length);
                accumulated += chars.slice(pos, end).join('');
                pos = end;
                $msg.html(self._markdownToHtml(accumulated));
                self.$messages.scrollTop(self.$messages.prop('scrollHeight'));
                if (pos < chars.length) {
                    setTimeout(tick, delay);
                } else {
                    $msg.removeClass('o_typing');
                    self._pushState({ type: 'message', role: 'assistant', text: text });
                    if (onDone) { onDone(); }
                }
            }

            tick();
        },

        _markdownToHtml: function (text) {
            // Escape HTML entities first
            var escaped = text
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;');

            // Markdown table rows: | col | col | → <tr><td>col</td>...
            escaped = escaped.replace(/^\|(.+)\|$/gm, function (_, inner) {
                var cells = inner.split('|').map(function (c) { return c.trim(); });
                return '<tr>' + cells.map(function (c) {
                    return /^[-\s:]+$/.test(c) ? '' : '<td>' + c + '</td>';
                }).join('') + '</tr>';
            });
            escaped = escaped.replace(/(<tr>.*<\/tr>\n?)+/g, function (block) {
                var rows = block.trim().split('\n').filter(function (r) { return r.trim(); });
                if (!rows.length) { return block; }
                var header = rows[0].replace(/<td>/g, '<th>').replace(/<\/td>/g, '</th>');
                var body = rows.slice(1).join('');
                return '<table class="o_mtr_chatbot_table"><thead>' + header + '</thead><tbody>' + body + '</tbody></table>';
            });

            // Headers: ## Title
            escaped = escaped.replace(/^### (.+)$/gm, '<h5>$1</h5>');
            escaped = escaped.replace(/^## (.+)$/gm, '<h4>$1</h4>');
            escaped = escaped.replace(/^# (.+)$/gm, '<h3>$1</h3>');

            // Bold and italic
            escaped = escaped.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
            escaped = escaped.replace(/\*(.+?)\*/g, '<em>$1</em>');

            // Bullet lists
            escaped = escaped.replace(/(^[ \t]*[-*] .+$\n?)+/gm, function (block) {
                var items = block.trim().split('\n').map(function (line) {
                    return '<li>' + line.replace(/^[ \t]*[-*] /, '') + '</li>';
                }).join('');
                return '<ul>' + items + '</ul>';
            });

            // Inline code
            escaped = escaped.replace(/`([^`]+)`/g, '<code>$1</code>');

            // Remaining line breaks outside block elements
            escaped = escaped.replace(/(?<!>)\n(?!<)/g, '<br>');

            return escaped;
        },

        _appendMessage: function (role, text) {
            var $msg = $('<div>', {
                class: 'o_mtr_chatbot_message o_mtr_chatbot_message_' + role,
            });
            if (role === 'assistant') {
                $msg.html(this._markdownToHtml(text));
            } else {
                $msg.text(text);
            }
            this.$messages.append($msg);
            this.$messages.scrollTop(this.$messages.prop('scrollHeight'));
            this._pushState({ type: 'message', role: role, text: text });
        },

        _appendResults: function (results) {
            var self = this;
            var count = results.length;

            var $container = $('<div>', { class: 'o_mtr_chatbot_results_container' });

            var $toggle = $('<button>', {
                type: 'button',
                class: 'btn btn-sm btn-outline-secondary o_mtr_chatbot_results_toggle',
            }).text(_t('Show Records (') + count + ')');

            var $wrap = $('<div>', { class: 'o_mtr_chatbot_results o_hidden' });

            $toggle.on('click', function () {
                var hidden = $wrap.hasClass('o_hidden');
                $wrap.toggleClass('o_hidden', !hidden);
                $toggle.text(hidden
                    ? _t('Hide Records (') + count + ')'
                    : _t('Show Records (') + count + ')');
            });

            results.slice().forEach(function (row) {
                var $card = $('<div>', { class: 'o_mtr_chatbot_result' });
                var title = [
                    row.mtr_batch_number || row.mtr_heat_number || row.inv_heat_number || '',
                    row.mtr_grade || row.inv_item_no || ''
                ].filter(Boolean).join(' • ');
                if (title) {
                    $card.append($('<div>', { class: 'o_mtr_chatbot_result_title' }).text(title));
                }
                var summary = [
                    row.inv_lot_number ? ('Lot: ' + row.inv_lot_number) : '',
                    row.inv_slab_number ? ('Slab: ' + row.inv_slab_number) : '',
                    row.mtr_certificate_number ? ('Cert: ' + row.mtr_certificate_number) : '',
                    row.join_status ? ('Status: ' + row.join_status) : ''
                ].filter(Boolean).join(' | ');
                if (summary) {
                    $card.append($('<div>', { class: 'o_mtr_chatbot_result_meta' }).text(summary));
                }

                if (row.missing_notes) {
                    $card.append($('<div>', { class: 'o_mtr_chatbot_result_meta' }).text('Match notes: ' + row.missing_notes));
                }

                var $actions = $('<div>', { class: 'o_mtr_chatbot_result_actions' });
                if (row.mtr_id) {
                    $actions.append(
                        $('<button>', {
                            type: 'button',
                            class: 'btn btn-sm btn-primary o_mtr_chatbot_open_mtr',
                            'data-id': row.mtr_id,
                        }).text(_t('Open MTR'))
                    );
                }
                if (row.join_id) {
                    $actions.append(
                        $('<button>', {
                            type: 'button',
                            class: 'btn btn-sm btn-secondary o_mtr_chatbot_open_join',
                            'data-id': row.join_id,
                        }).text(_t('Open Join Report'))
                    );
                }
                if (row.inventory_id) {
                    $actions.append(
                        $('<button>', {
                            type: 'button',
                            class: 'btn btn-sm btn-secondary o_mtr_chatbot_open_inventory',
                            'data-id': row.inventory_id,
                        }).text(_t('Open Inventory'))
                    );
                }
                $card.append($actions);
                $wrap.append($card);
            });

            $container.append($toggle).append($wrap);
            this.$messages.append($container);
            this.$messages.scrollTop(this.$messages.prop('scrollHeight'));
            this._pushState({ type: 'results', results: results });
        },

        _appendBranchChoices: function (branches) {
            var self = this;
            var $wrap = $('<div>', { class: 'o_mtr_chatbot_branch_choices' });
            $wrap.append($('<div>', { class: 'o_mtr_chatbot_message o_mtr_chatbot_message_assistant' }).text(_t('Choose the branch to match:')));
            branches.forEach(function (branch) {
                var label = branch.name || branch.branch_key || _t('Select branch');
                var $btn = $('<button>', {
                    type: 'button',
                    class: 'btn btn-sm btn-primary o_mtr_chatbot_choose_branch',
                    'data-branch-id': branch.id,
                    'data-branch-name': branch.name || branch.branch_key || '',
                }).text(label || _t('Select branch'));
                $wrap.append($btn);
            });
            this.$messages.append($wrap);
            this.$messages.scrollTop(this.$messages.prop('scrollHeight'));
        },

        _onChooseBranch: function (ev) {
            var $btn = $(ev.currentTarget);
            var branchId = parseInt($btn.data('branch-id'), 10);
            if (!branchId) {
                return;
            }
            var branchName = $btn.data('branch-name') || '';
            this._branchId = branchId;
            this._appendMessage('user', branchName ? ('branch ' + branchName) : ('branch ' + branchId));
            this._runMatchFor(this._specName || '', branchId);
        },

        _onOpenJoin: function (ev) {
            var id = parseInt($(ev.currentTarget).data('id'), 10);
            if (!id) {
                return;
            }
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: 'mtr.inventory.join.report',
                res_id: id,
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'current',
            });
        },

        _onOpenInventory: function (ev) {
            var id = parseInt($(ev.currentTarget).data('id'), 10);
            if (!id) {
                return;
            }
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: 'inventory.record',
                res_id: id,
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'current',
            });
        },

        _onOpenMtr: function (ev) {
            var id = parseInt($(ev.currentTarget).data('id'), 10);
            if (!id) {
                return;
            }
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: 'mtr.data',
                res_id: id,
                view_mode: 'form',
                views: [[false, 'form']],
                target: 'current',
            });
        },

        _onClear: function () {
            this.$messages.empty();
            window.sessionStorage.removeItem(this._stateKey);
            this._appendMessage('assistant', _t('Hi! Ask me about an MTR by batch number, grade, or chemical specs.'));
        },

        _autoMatchFromContext: function () {
            if (this._autoMatched) {
                return;
            }
            var specName = this._specName || this._getSpecNameFromContext();
            var specId = this._specId || this._getSpecIdFromContext();
            if (!specName && !specId) {
                return;
            }
            this._autoMatched = true;
            var self = this;
            if (specName) {
                this._appendMessage('assistant', _t('Running match for: ') + specName);
                setTimeout(function () {
                    self._appendMessage('user', 'match ' + specName);
                    self._runMatchFor(specName);
                }, 50);
            } else {
                rpc.query({
                    route: '/mtr_module/spec_name',
                    params: { spec_id: specId },
                }).then(function (resp) {
                    var name = (resp && resp.name) ? resp.name : '';
                    if (!name) {
                        self._appendMessage('assistant', _t('I could not resolve the spec name from context.'));
                        return;
                    }
                    self._specName = name;
                    self._renderContext();
                    self._appendMessage('assistant', _t('Running match for: ') + name);
                    self._appendMessage('user', 'match ' + name);
                    self._runMatchFor(name);
                });
            }
        },

        _allContexts: function () {
            // Collect all context/param sources and merge them so no single
            // truthy-but-empty object blocks the others via || chaining.
            var sources = [
                this.action && this.action.context,
                this.action && this.action.params,
                this.options && this.options.context,
                this.options && this.options.params,
                this.options && this.options.action && this.options.action.context,
                this.options && this.options.action && this.options.action.params,
                this.context,
                (this.getContext && this.getContext()),
            ];
            var merged = {};
            sources.forEach(function (s) {
                if (s && typeof s === 'object') {
                    Object.keys(s).forEach(function (k) {
                        if (merged[k] === undefined || merged[k] === null || merged[k] === '') {
                            merged[k] = s[k];
                        }
                    });
                }
            });
            return merged;
        },

        _getSpecNameFromContext: function () {
            var ctx = this._allContexts();
            return ctx.match_spec_name || ctx.planner_spec_name || ctx.spec_name || '';
        },

        _getSpecIdFromContext: function () {
            var ctx = this._allContexts();
            return ctx.match_spec_id || ctx.planner_spec_id || ctx.spec_id || '';
        },

        _getBranchIdFromContext: function () {
            var ctx = this._allContexts();
            return ctx.branch_id || ctx.match_branch_id || '';
        },

        _shouldResetStateFromContext: function () {
            var ctx = this._allContexts();
            return Boolean(ctx.match_reset_state);
        },

        _getModeFromContext: function () {
            var ctx = (this.getContext && this.getContext()) ||
                (this.context) ||
                (this.action && this.action.context) ||
                (this.options && this.options.context) ||
                (this.options && this.options.action && this.options.action.context) ||
                {};
            var params = (this.action && this.action.params) ||
                (this.options && this.options.params) ||
                (this.options && this.options.action && this.options.action.params) ||
                {};
            var mode = ctx.mode || params.mode || (ctx.planner_mode || params.planner_mode ? 'planner' : '');
            return String(mode || '').toLowerCase();
        },

        _renderContext: function () {
            var $ctx = this.$('.o_mtr_chatbot_context');
            if (!$ctx || !$ctx.length) {
                return;
            }
            var ctx = (this.context) ||
                (this.action && this.action.context) ||
                (this.options && this.options.context) ||
                (this.options && this.options.action && this.options.action.context) ||
                {};
            var params = (this.action && this.action.params) ||
                (this.options && this.options.action && this.options.action.params) ||
                {};
            if (this._specName) {
                $ctx.text(this._plannerMode ? ('Planner Spec: ' + this._specName) : ('Spec: ' + this._specName));
            } else {
                $ctx.text('');
            }
        },

        _applyModeUi: function () {
            var $header = this.$('.o_mtr_chatbot_header');
            var $input = this.$('.o_mtr_chatbot_input_text');
            var $send = this.$('.o_mtr_chatbot_send');
            if ($header && $header.length) {
                $header.text(this._plannerMode ? _t('MTR Filter Planner') : _t('MTR Chatbot'));
            }
            if ($input && $input.length) {
                $input.attr(
                    'placeholder',
                    this._plannerMode
                        ? _t('Example: explain custom rule quality must_comply A6, A29')
                        : _t('Example: Heat number H100 or C >= 0.20, Mn 1.1')
                );
            }
            if ($send && $send.length) {
                $send.text(this._plannerMode ? _t('Plan') : _t('Ask'));
            }
        },

        _autoPlanFromContext: function () {
            var self = this;
            if (!this._plannerMode || !this._specId) {
                return;
            }
            setTimeout(function () {
                self._appendMessage('user', 'plan ' + (self._specName || self._specId));
                self._runPlanFor(self._specName || self._specId);
            }, 50);
        },

        _autoPlanFromLastSpec: function () {
            if (!this._plannerMode || this._specId) {
                return;
            }
            var self = this;
            rpc.query({
                route: '/mtr_module/last_spec',
                params: {},
            }).then(function (resp) {
                if (!resp || !resp.id || self._specId) {
                    return;
                }
                self._specId = resp.id;
                self._specName = resp.name || self._specName;
                self._renderContext();
                setTimeout(function () {
                    self._appendMessage('user', 'plan ' + resp.name);
                    self._runPlanFor(resp.name);
                }, 50);
            });
        },

        _bootstrapMatchFlow: function () {
            var self = this;
            rpc.query({
                route: '/mtr_module/pending_match',
                params: {},
            }).then(function (resp) {
                if (!resp || !resp.id) {
                    // No pending match — plain chatbot open, stay silent
                    return;
                }
                self._specId = resp.id;
                self._specName = resp.name || String(resp.id);
                self._renderContext();
                self._appendMessage('assistant', _t('Running match for: ') + self._specName);
                setTimeout(function () {
                    self._appendMessage('user', 'match ' + self._specName);
                    self._runMatchFor(self._specName);
                }, 200);
            }).guardedCatch(function () {
                // Silent fail — just let the user use the chatbot normally
            });
        },

        _runMatchFor: function (specName, branchId) {
            var text = 'match ' + specName;
            this._setLoading(true);
            var debugLlm = window.location.search.indexOf('debug_llm=1') !== -1;
            var self = this;
            rpc.query({
                route: '/mtr_module/mtr_chatbot',
                params: { message: text, debug_llm: debugLlm, spec_id: this._specId, branch_id: branchId || this._branchId },
            }).then(function (response) {
                self._setLoading(false);
                if (response && response.error) {
                    self._appendMessage('assistant', response.error);
                    return;
                }
                if (response && response.need_branch && response.branches && response.branches.length) {
                    self._appendMessage('assistant', response.answer || _t('Please choose a branch to continue.'));
                    self._appendBranchChoices(response.branches);
                    return;
                }
                if (response && response.debug_llm) {
                    self._appendMessage('assistant', 'LLM raw: ' + response.debug_llm);
                }
                if (response && response.answer) {
                    self._appendMessage('assistant', response.answer);
                }
                if (response && response.results && response.results.length) {
                    self._appendResults(response.results);
                } else if (!response || (!response.answer && !response.error)) {
                    self._appendMessage('assistant', _t('No matching records found.'));
                }
            }).guardedCatch(function () {
                self._setLoading(false);
                self._appendMessage('assistant', _t('Something went wrong. Please try again.'));
            });
        },

        _runPlanFor: function (promptText) {
            this._setLoading(true);
            var debugLlm = window.location.search.indexOf('debug_llm=1') !== -1;
            var self = this;
            rpc.query({
                route: '/mtr_module/spec_filter_plan',
                params: {
                    spec_id: this._specId,
                    message: promptText || '',
                    debug_llm: debugLlm,
                },
            }).then(function (response) {
                self._setLoading(false);
                if (response && response.error) {
                    self._appendMessage('assistant', response.error);
                    return;
                }
                if (response && response.debug_llm) {
                    self._appendMessage('assistant', 'LLM raw: ' + response.debug_llm);
                }
                if (response && response.answer) {
                    self._appendMessage('assistant', response.answer);
                } else {
                    self._appendMessage('assistant', _t('No filtering plan returned.'));
                }
            }).guardedCatch(function () {
                self._setLoading(false);
                self._appendMessage('assistant', _t('Something went wrong. Please try again.'));
            });
        },

        _getState: function () {
            var raw = window.sessionStorage.getItem(this._stateKey);
            if (!raw) {
                return null;
            }
            try {
                var parsed = JSON.parse(raw);
                return Array.isArray(parsed) ? parsed : null;
            } catch (e) {
                return null;
            }
        },

        _saveState: function (state) {
            window.sessionStorage.setItem(this._stateKey, JSON.stringify(state));
        },

        _pushState: function (entry) {
            if (this._restoring) {
                return;
            }
            var state = this._getState() || [];
            state.push(entry);
            this._saveState(state);
        },

        _restoreState: function () {
            var state = this._getState();
            if (!state || !state.length) {
                return false;
            }
            var self = this;
            state.forEach(function (entry) {
                if (entry.type === 'message') {
                    self._appendMessage(entry.role, entry.text);
                } else if (entry.type === 'results' && entry.results) {
                    self._appendResults(entry.results);
                }
            });
            return true;
        },
    });

    core.action_registry.add('mtr_module.mtr_chatbot_action', MtrChatbot);
    core.action_registry.add('mtr_module.mtr_spec_planner_action', MtrChatbot);

    return MtrChatbot;
});
