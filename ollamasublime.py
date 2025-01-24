import sublime
import sublime_plugin
import requests
import json
import threading
import datetime

class OllamaSublimeSelectModelCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        settings = sublime.load_settings('OllamaSublime.sublime-settings')
        url = settings.get('ollamaUrl', 'http://localhost:11434')
        
        try:
            response = requests.get("{0}/api/tags".format(url))
            models = [model['name'] for model in response.json()['models']]
            
            def on_done(index):
                if index >= 0:
                    settings.set('selected_model', models[index])
                    sublime.save_settings('OllamaSublime.sublime-settings')
            
            sublime.active_window().show_quick_panel(models, on_done)
        except Exception as e:
            sublime.error_message("Error fetching models: {0}".format(str(e)))

class OllamaSublimeAskAnyCommand(sublime_plugin.TextCommand):
    def run(self, edit, prompt=None):
        if not prompt:
            self.view.window().show_input_panel("Enter your prompt:", "", 
                self.on_prompt_done, None, None)
        else:
            self.on_prompt_done(prompt)
    
    def on_prompt_done(self, prompt):
        if prompt:
            # Get settings
            settings = sublime.load_settings('OllamaSublime.sublime-settings')
            
            # Get current history
            history = settings.get('history', [])
            
            # Create new entry
            new_entry = {
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'prompt': prompt,
                'model': settings.get('selected_model')
            }
            
            # Remove any existing entries with the same prompt (case-insensitive)
            history = [h for h in history if h['prompt'].lower() != prompt.lower()]
            
            # Add new entry at the beginning
            history.insert(0, new_entry)
            
            # Keep only last 50 items
            if len(history) > 50:
                history = history[0:50]
            
            # Save updated history
            settings.set('history', history)
            sublime.save_settings('OllamaSublime.sublime-settings')
            
            # Continue with request...
            model = settings.get('selected_model')
            if not model:
                sublime.error_message("Please select a model first")
                return
            
            system_prompt = settings.get('systemPrompt', 'You are a helpful assistant.')
            url = settings.get('ollamaUrl', 'http://localhost:11434')
            
            sel = self.view.sel()
            if len(sel[0]) > 0:
                # Get selection
                context = self.view.substr(sel[0])
                # Store the insertion point
                insert_point = sel[0].end()
                # Clear the selection
                self.view.sel().clear()
                # Insert two newlines after the previous selection
                self.view.run_command('insert', {'characters': '\n\n'})
                # Place cursor at the new position
                self.view.sel().add(sublime.Region(insert_point + 2))
            else:
                context = self.view.substr(sublime.Region(0, self.view.size()))
            
            thread = OllamaRequestThread(self.view, url, model, system_prompt, prompt, context)
            thread.start()

class OllamaSublimeUseTemplateCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        settings = sublime.load_settings('OllamaSublime.sublime-settings')
        templates = settings.get('templates', [])
        
        if not templates:
            sublime.error_message("No templates defined in settings")
            return
            
        items = ["{0} - {1}".format(
            t['title'], 
            t['prompt'][:50] + "..." if len(t['prompt']) > 50 else t['prompt']
        ) for t in templates]
        
        def on_done(index):
            if index >= 0:
                self.template = templates[index]
                model = self.template.get('model', settings.get('selected_model'))
                if not model:
                    sublime.error_message("No model selected or specified in template")
                    return
                    
                settings.set('selected_model', model)
                self.view.window().show_input_panel(
                    "Edit prompt:", 
                    self.template['prompt'],
                    self.on_prompt_edited,
                    None,
                    None
                )
        
        sublime.active_window().show_quick_panel(items, on_done)
    
    def on_prompt_edited(self, edited_prompt):
        if edited_prompt:
            self.view.run_command('ollama_sublime_ask_any', {'prompt': edited_prompt})

class OllamaSublimeAddTemplateCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        self.settings = sublime.load_settings('OllamaSublime.sublime-settings')
        window = sublime.active_window()
        window.show_input_panel("Template Title:", "", self.on_title_done, None, None)
    
    def on_title_done(self, title):
        self.title = title
        # Get available models
        url = self.settings.get('ollamaUrl', 'http://localhost:11434')
        try:
            response = requests.get("{0}/api/tags".format(url))
            self.models = [model['name'] for model in response.json()['models']]
            self.models.insert(0, "Use Default Model")  # Add option to use default model
            
            # Show model selection
            sublime.active_window().show_quick_panel(self.models, self.on_model_done)
        except Exception as e:
            print("OllamaSublime Error: {0}".format(str(e)))
            # Continue without model selection
            self.on_prompt_input()
    
    def on_model_done(self, index):
        if index > 0:  # If a specific model was selected
            self.model = self.models[index]
        else:
            self.model = None
        self.on_prompt_input()
    
    def on_prompt_input(self):
        window = sublime.active_window()
        window.show_input_panel("Template Prompt:", "", self.on_prompt_done, None, None)
    
    def on_prompt_done(self, prompt):
        templates = self.settings.get('templates', [])
        
        # Create template object
        template = {
            "title": self.title,
            "prompt": prompt
        }
        
        # Add model if one was selected
        if hasattr(self, 'model') and self.model:
            template["model"] = self.model
        
        # Add new template
        templates.append(template)
        
        self.settings.set('templates', templates)
        sublime.save_settings('OllamaSublime.sublime-settings')
        sublime.status_message("Template added successfully")

class OllamaSublimeRemoveTemplateCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        settings = sublime.load_settings('OllamaSublime.sublime-settings')
        templates = settings.get('templates', [])
        
        if not templates:
            sublime.error_message("No templates to remove")
            return
        
        # Create list items with preview
        items = ["{0} - {1}".format(
            t['title'], 
            t['prompt'][:50] + "..." if len(t['prompt']) > 50 else t['prompt']
        ) for t in templates]
        
        def on_done(index):
            if index >= 0:
                templates.pop(index)
                settings.set('templates', templates)
                sublime.save_settings('OllamaSublime.sublime-settings')
                sublime.status_message("Template removed successfully")
        
        sublime.active_window().show_quick_panel(items, on_done)

class OllamaSublimeEditTemplateCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        self.settings = sublime.load_settings('OllamaSublime.sublime-settings')
        templates = self.settings.get('templates', [])
        
        if not templates:
            sublime.error_message("No templates defined in settings")
            return
        
        # Create list items with preview
        self.items = ["{0} - {1}".format(
            t['title'], 
            t['prompt'][:50] + "..." if len(t['prompt']) > 50 else t['prompt']
        ) for t in templates]
        
        # Store templates for later use
        self.templates = templates
        
        # Show template selection
        sublime.active_window().show_quick_panel(self.items, self.on_template_selected)
    
    def on_template_selected(self, index):
        if index >= 0:
            self.selected_index = index
            self.template = self.templates[index]
            
            # Show input panel for editing title
            sublime.active_window().show_input_panel(
                "Edit template title:",
                self.template['title'],
                self.on_title_done,
                None,
                None
            )
    
    def on_title_done(self, title):
        if title:
            self.new_title = title
            
            # Get available models
            url = self.settings.get('ollamaUrl', 'http://localhost:11434')
            try:
                response = requests.get("{0}/api/tags".format(url))
                self.models = [model['name'] for model in response.json()['models']]
                self.models.insert(0, "Use Default Model")
                if self.template.get('model'):
                    self.models.insert(1, "Keep Current Model ({0})".format(self.template['model']))
                
                # Show model selection
                sublime.active_window().show_quick_panel(self.models, self.on_model_done)
            except Exception as e:
                print("OllamaSublime Error: {0}".format(str(e)))
                # Continue without model selection
                self.on_prompt_input()
    
    def on_model_done(self, index):
        if index == 0:  # Use Default Model
            self.new_model = None
        elif index == 1 and self.template.get('model'):  # Keep current model
            self.new_model = self.template['model']
        elif index > 0:  # New model selected
            offset = 2 if self.template.get('model') else 1
            self.new_model = self.models[index]
        else:  # Cancelled
            self.new_model = self.template.get('model')
        
        self.on_prompt_input()
    
    def on_prompt_input(self):
        # Show input panel for editing prompt
        sublime.active_window().show_input_panel(
            "Edit template prompt:",
            self.template['prompt'],
            self.on_prompt_done,
            None,
            None
        )
    
    def on_prompt_done(self, prompt):
        if prompt:
            # Update template
            new_template = {
                "title": self.new_title,
                "prompt": prompt
            }
            
            # Add model if specified
            if self.new_model:
                new_template["model"] = self.new_model
            
            # Update template in list
            self.templates[self.selected_index] = new_template
            
            # Save updated templates
            self.settings.set('templates', self.templates)
            sublime.save_settings('OllamaSublime.sublime-settings')
            sublime.status_message("Template updated successfully")

class OllamaSublimeRequestManager:
    _instance = None
    _current_thread = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def set_current_thread(self, thread):
        self._current_thread = thread
    
    def cancel_current_request(self):
        if self._current_thread and self._current_thread.is_alive():
            self._current_thread.cancel()
            return True
        return False

class OllamaSublimeCancelRequestCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        manager = OllamaSublimeRequestManager.get_instance()
        if manager.cancel_current_request():
            sublime.status_message("OllamaSublime: Request cancelled")
        else:
            sublime.status_message("OllamaSublime: No active request to cancel")

class OllamaRequestThread(threading.Thread):
    def __init__(self, view, url, model, system_prompt, prompt, context):
        threading.Thread.__init__(self)
        self.view = view
        self.url = url
        self.model = model
        self.system_prompt = system_prompt
        self.prompt = prompt
        self.context = context
        self.cancelled = False
        self.response = None
        
        # Register as current thread
        OllamaSublimeRequestManager.get_instance().set_current_thread(self)

    def cancel(self):
        self.cancelled = True
        if self.response:
            try:
                self.response.close()
            except:
                pass  # Ignore any errors during close

    def run(self):
        try:
            sublime.set_timeout(
                lambda: self.view.set_status('ollama', 'OllamaSublime: Generating response with {0}... (Press Cmd/Ctrl+Shift+C to cancel)'.format(self.model)),
                0
            )
            
            print("OllamaSublime: Making request to {0}".format(self.url))
            print("OllamaSublime: Using model: {0}".format(self.model))
            
            try:
                self.response = requests.post(
                    "{0}/api/generate".format(self.url),
                    json={
                        "model": self.model,
                        "system": self.system_prompt,
                        "prompt": "{0}\n\n{1}".format(self.context, self.prompt),
                        "stream": True
                    },
                    stream=True
                )

                for line in self.response.iter_lines():
                    if self.cancelled:
                        print("OllamaSublime: Request cancelled by user")
                        sublime.set_timeout(
                            lambda: self.view.erase_status('ollama'),
                            0
                        )
                        return
                        
                    if line:
                        data = json.loads(line.decode('utf-8'))
                        if 'response' in data:
                            sublime.set_timeout(
                                lambda x=data['response']: self.view.run_command('ollama_insert_text', {'text': x}),
                                0
                            )
            finally:
                if self.response:
                    try:
                        self.response.close()
                    except:
                        pass
                
                # Always clear the status bar
                sublime.set_timeout(
                    lambda: self.view.erase_status('ollama'),
                    0
                )
                
        except Exception as e:
            if not self.cancelled:
                print("OllamaSublime Error: {0}".format(str(e)))
                sublime.error_message("Error making request: {0}".format(str(e)))
            # Clear status even on error
            sublime.set_timeout(
                lambda: self.view.erase_status('ollama'),
                0
            )

class OllamaInsertTextCommand(sublime_plugin.TextCommand):
    def run(self, edit, text):
        sel = self.view.sel()
        if sel:
            self.view.insert(edit, sel[0].begin(), text)

class OllamaSublimeShowHistoryCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        settings = sublime.load_settings('OllamaSublime.sublime-settings')
        history = settings.get('history', [])
        
        if not history:
            sublime.error_message("No history available")
            return
        
        # Sort history by timestamp (newest first)
        history = sorted(
            history,
            key=lambda x: datetime.datetime.strptime(x['timestamp'], '%Y-%m-%d %H:%M:%S'),
            reverse=True
        )
        
        # Create list items with preview and timestamp
        items = ["{0} - {1}".format(
            h['timestamp'],
            h['prompt'][:50] + "..." if len(h['prompt']) > 50 else h['prompt']
        ) for h in history]
        
        def on_done(index):
            if index >= 0:
                # Get the selected history item
                selected = history[index]
                
                # Show input panel with historical prompt for editing
                self.view.window().show_input_panel(
                    "Edit prompt:", 
                    selected['prompt'],
                    lambda prompt: self.view.run_command('ollamasublime_ask_any', {'prompt': prompt}),
                    None,
                    None
                )
        
        sublime.active_window().show_quick_panel(items, on_done)

class OllamaSublimeClearHistoryCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        settings = sublime.load_settings('OllamaSublime.sublime-settings')
        settings.set('history', [])
        sublime.save_settings('OllamaSublime.sublime-settings')
        sublime.status_message("OllamaSublime: History cleared")