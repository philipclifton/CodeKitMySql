import sublime_plugin
import subprocess
import sublime

matches = []
tables = []
getTableDb = ''

s = sublime.load_settings('CodekitMysql.sublime-settings');

class show_whole_table(sublime_plugin.TextCommand):
	tables = []
	selCol = '';
	def run(self, args):
		self.tables = getTables(self.view)
		self.view.window().show_quick_panel(self.tables, self.tableSelected);

	def tableSelected(self, index):
		# Get Table
		table = self.tables[index];
		# Get database setting 
		database = self.view.window().project_data()['database'];

		command = str(s.get('mysql_executable')) + " -e 'SELECT * FROM {2}.{3}' --raw -E -u {0} -p{1}".format(str(s.get('mysql_user')), str(s.get('mysql_pass')), str(database), str(table));
		output = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
		out, err = output.communicate()
		
		if out:
			view = sublime.active_window().new_file()
			view.run_command('append', {
			    'characters': out.decode('utf-8'),
			    })

class show_single_row(sublime_plugin.TextCommand):
	def run(self, args):
		self.tables = getTables(self.view)
		self.view.window().show_quick_panel(self.tables, self.tableSelected);

	def tableSelected(self, index):
		
		# Get Table
		self.table = self.tables[index];

		# Get database setting 
		self.database = self.view.window().project_data()['database'];

		# Setup cols
		self.cols = [];

		s = sublime.load_settings('CodekitMysql.sublime-settings');

		# Command to get columns out! 
		command = str(s.get('mysql_executable')) + " -e 'show columns from {2}.{3}' --raw -u {0} -p{1}".format(str(s.get('mysql_user')), str(s.get('mysql_pass')), str(self.database), str(self.table));
		print(command)
		output = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
		out, err = output.communicate()

		if out:
			# Raw is dirty - get table name
			rawTables = out.decode('utf-8').split('\n')
			for rawTable in rawTables:
				cols = rawTable.split('\t')
				col = cols[0];
				if col:
					self.cols.append(col);

			sublime.set_timeout(lambda: self.view.window().show_quick_panel(self.cols, self.whereStatment), 0)
				
	def whereStatment(self, index):	
		if index >= 0:
			self.view.window().show_input_panel('Where', self.cols[index] + '=', self.result, False, False);

	def result(self, value):

		s = sublime.load_settings('CodekitMysql.sublime-settings');

		command = str(s.get('mysql_executable')) + " -e 'SELECT * FROM {2}.{3} WHERE {4}' --raw -E -u {0} -p{1}".format(str(s.get('mysql_user')), str(s.get('mysql_pass')), str(self.database), str(self.table), str(value));
		output = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
		out, err = output.communicate()
		
		if out:
			view = sublime.active_window().new_file()
			view.run_command('append', {
			    'characters': out.decode('utf-8'),
			    })	

		if err:
			print(err.decode('utf-8'))	

class show_between(sublime_plugin.TextCommand):
	table = ''
	database = ''
	
	def run(self, args):
		show_between.tables = getTables(self.view)

		show_between.database = self.view.window().project_data()['database'];
		self.view.window().show_quick_panel(self.tables, self.setLimit);

	def setLimit(self, index):
		if index >= 0:
			# Get Table
			show_between.table = show_between.tables[index];

			# Get database setting 
			self.view.window().show_input_panel('Limit', '0,' , self.result, None, None);
				
	def result(self, limit):
		# Run SQL
		command = str(s.get('mysql_executable')) + " -e 'SELECT * FROM {2}.{3} LIMIT {4}' --raw -E -u {0} -p{1}".format(str(s.get('mysql_user')), str(s.get('mysql_pass')), str(show_between.database), str(show_between.table), str(limit));
		output = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
		out, err = output.communicate()
		if out:
			view = sublime.active_window().new_file()
			view.run_command('append', {
			    'characters': out.decode('utf-8'),
			    })		


class CodekitMysql(sublime_plugin.EventListener):
	def on_activated_async(self, view):

		# Get tables
		tables = getTables(view)

		# Get Database
		database = view.window().project_data()['database'];

		# for each table run show cols and add to matches array
		for table in tables:
			if table:
				
				if table not in matches:
					matches.append(table)

				command = str(s.get('mysql_executable')) + " -e 'show columns from {2}.{3}' --raw -u {0} -p'{1}'".format(str(s.get('mysql_user')), str(s.get('mysql_pass')), str(database), str(table));

				output = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
				out, err = output.communicate()
				
				if out:
					# Raw is dirty - get table name
					rawTables = out.decode('utf-8').split('\n')
					for rawTable in rawTables:
						cols = rawTable.split('\t')
						col = cols[0];
						if col:
							if col not in matches:
								matches.append(col);
							if '{0}.{1}'.format(table, col) not in matches:
								matches.append('{0}.{1}'.format(table, col))

	def on_query_completions(self, view, prefix, locations):
		words = without_duplicates(matches)
		display = [(w, w) for w in words]
		return display


def without_duplicates(words):
    result = []
    for w in words:
        if w not in result:
            result.append(w)
    return result


def getTables(view):
	if 'database' in view.window().project_data():

		s = sublime.load_settings('CodekitMysql.sublime-settings');

		getTableDb = view.window().project_data()['database'];

		# Command to go get database tables!
		command = str(s.get('mysql_executable')) + " -e 'show tables from {2}' -u {0} -p'{1}'".format(str(s.get('mysql_user')), str(s.get('mysql_pass')), str(getTableDb));

		# Run table command
		output = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
		out, err = output.communicate()

		# Empty tables
		tables = [];

		# If succesful command
		if out:
			# Split and add populate arraay
			tables = out.decode('utf-8').split('\n');
			return tables;
