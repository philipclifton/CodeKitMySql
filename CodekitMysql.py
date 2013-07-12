import sublime_plugin
import subprocess
import sublime

matches = []

class CodekitMysql(sublime_plugin.EventListener):
	tables = []
	def on_activated_async(self, view):

		# EMPTY MATCHES
		# matches = []

		# Project have database set?
		if 'database' in view.window().project_data():

			# Get database setting 
			database = view.window().project_data()['database'];

			# Load Settings Files
			s = sublime.load_settings('CodekitMysql.sublime-settings');

			# Command to go get database tables!
			command = s.get('mysql_executable') + " -e 'show tables from {2}' -u {0} -p'{1}'".format(s.get('mysql_user'), s.get('mysql_pass'), database);

			# Run table command
			output = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
			out, err = output.communicate()

			# Empty tables
			self.tables = [];

			# If succesful command
			if out:

				# Split and add populate arraay
				self.tables = out.decode('utf-8').split('\n');
				# for each table run show cols and add to matches array
				for table in self.tables:
					if table:
						
						matches.append(table)

						# Command to get columns out! 
						command = s.get('mysql_executable') + " -e 'show columns from {2}.{3}' --raw -u {0} -p{1}".format(s.get('mysql_user'), s.get('mysql_pass'), database, table);
						output = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
						out, err = output.communicate()
						
						if out:
						
							# Raw is dirty - get table name
							rawTables = out.decode('utf-8').split('\n')
							for rawTable in rawTables:
								cols = rawTable.split('\t')
								col = cols[0];
								if col:
									matches.append(col);
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
