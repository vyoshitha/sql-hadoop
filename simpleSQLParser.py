class SimpleSQLParser:
    QUERY = None
    DICTIONARY = None

    """
        Constructor Function.
    """

    def __init__(self):
        self.QUERY = None
        self.DICTIONARY = dict()

    """
        Setter function for QUERY.
    """

    def addQuery(self, query):
        self.QUERY = query

    """
        Getter function for DICTIONARY.
    """

    def getParsedQuery(self):
        return self.DICTIONARY

    """
        Function to clear the DICTIONARY
        and insert the ERROR.
    """

    def clearAndMakeError(self, error):
        self.DICTIONARY = dict()
        self.DICTIONARY['error'] = error
        return 0

    """
        Function to check syntax of query.
    """

    def checkSyntax(self, query, strict=False, syntax_to_be_checked=None):
        # Check if STRICT mode is ON => In which case, see if the
        # query ends with a semicolon (;)
        if self.QUERY.lower().strip(" ").endswith(";") and not strict:
            return self.clearAndMakeError("Use strict=True in parseQuery().")
        if syntax_to_be_checked is None and strict:
            if not self.QUERY.lower().strip(" ").endswith(";"):
                return self.clearAndMakeError("Syntax error. [STRICT ON]")
            else:
                # If test passed, remove the ending semicolon (;)
                self.QUERY = self.QUERY[:-1]

        # Default check: Allow only SELECT/LOAD queries.
        if syntax_to_be_checked is None or syntax_to_be_checked == "type":
            if not self.DICTIONARY['type'].lower() == "select" and not self.DICTIONARY['type'].lower() == "load":
                return self.clearAndMakeError("Supported only SELECT/LOAD queries.")

        # Check if SELECT queries end with a comma
        if syntax_to_be_checked == "select_column_names":
            if query.strip(" ").endswith(","):
                return self.clearAndMakeError("Incorrect Syntax. (incomplete column names)")

        return 1

    """
        Function to detect the type of query based 
        on first word.
    """

    def parseQueryType(self):
        type_of_query = self.QUERY.split(" ")[0]
        self.DICTIONARY['type'] = type_of_query

    """
        Function to parse the QUERY.
    """

    def parseQuery(self, query, strict=False):
        # First, set the QUERY variable.
        self.addQuery(query)
        # Then, set the QUERY TYPE.
        self.parseQueryType()
        # Check if all default syntax tests pass.
        if self.checkSyntax(self.QUERY, strict=strict):
            # If it is a SELECT query, then enter this flow.
            if self.DICTIONARY['type'].lower() == "select":
                # Get selected Columns and their names in an array.
                if self.getSelectedColumnNames(self.QUERY):
                    # Get optional WHERE Clauses in a dictionary.
                    if self.getWHEREClauses(self.QUERY):
                        return self.DICTIONARY
            elif self.DICTIONARY['type'].lower() == "load":
                # This is a load query, enter this flow.
                if self.parseLOADDatabase(self.QUERY):
                    return self.DICTIONARY

    """
        Function to define the WHERE clauses dictionary.
        This function returns two keys: AND, OR - both
        of which are arrays, and contain clauses under them.
    """

    def getWHEREClauses(self, query):
        clauses = dict()
        clauses['AND'] = list()
        clauses['OR'] = list()

        # Immediately exit if there is already an error.
        # TODO: Why does this condition arrive in the first place?
        if 'error' in self.DICTIONARY:
            return 0

        try:
            # Check if there is WHERE clause.
            len_where = len(query[:query.lower().index("where", len(self.DICTIONARY['type']))])

            try:
                # Check if the query has any brackets,
                # If yes - immediately raise an error.
                bracket_open = query[len_where + 5:].index("(", 0)
                bracket_close = query[len_where + 5:].index(")", 0)

                return self.clearAndMakeError("This parser does not support brackets.")
            except ValueError:
                # All basic tests passed, proceed to
                # get the WHERE query.
                clause_query = query[len_where + 5:]

                # Split the WHERE query based on ANDs.
                clauses['AND'] = clause_query.lower().split(" and ")

                # Loop through each elements of the AND array.
                for index in range(len(clauses['AND'])):
                    # Strip empty spaces from both ends.
                    clauses['AND'][index] = clauses['AND'][index].strip(" ")

                    # Further divide the query using OR clause.
                    or_clauses = clauses['AND'][index].lower().split(" or ")

                    # If only ONE OR clause exists,
                    # Just append them into OR array.
                    # Example: "... WHERE this = that OR that = this;"
                    if len(clauses['AND']) == 1:
                        if len(or_clauses) > 1:
                            clauses['AND'] = list()
                            clauses['OR'] = or_clauses
                        else:
                            clauses['AND'] = or_clauses
                            clauses['OR'] = list()
                    else:
                        # This means we have either 0, or
                        # more than 2 elements.
                        # (1 was already covered)
                        if len(or_clauses) == 2:
                            # If length is 2, then delete this
                            # element in the AND array.
                            # Add the left most bit to the
                            # AND Array, and the remaining
                            # in the OR Array.
                            # Example: "... WHERE a = b AND c = d OR d = e;"
                            # Here, AND: {"a = b", "c = d"}
                            # OR = {"d = e"}
                            del clauses['AND'][index]
                            clauses['AND'] = clauses['AND'] + or_clauses[1:]
                            # del or_clauses[0] => Commented because (a or b and c) => a or (b and c)
                            clauses['OR'] = clauses['OR'] + or_clauses[0:1]
                        elif len(or_clauses) > 2:
                            # If more than 2 elements,
                            # just append to OR array.
                            del clauses['AND'][index]
                            clauses['OR'] = clauses['OR'] + or_clauses

                # This loop goes through every element of
                # AND array, and strips their ";"s, and also
                # checks for dummy elements: in which case
                # exit, and show error.
                for index in range(len(clauses['AND'])):
                    if clauses['AND'][index].endswith(";"):
                        clauses['AND'][index] = clauses['AND'][index][:len(clauses['AND'][index]) - 1]

                    if len(clauses['AND'][index]) == 0:
                        return self.clearAndMakeError("Incorrect Syntax.")

                # Same loop as above, but for OR array.
                for index in range(len(clauses['OR'])):
                    if clauses['OR'][index].endswith(";"):
                        clauses['OR'][index] = clauses['OR'][index][:len(clauses['OR'][index]) - 1]

                    if len(clauses['OR'][index]) == 0:
                        return self.clearAndMakeError("Incorrect Syntax.")

        except ValueError:
            # This condition happens when there is NO where clause.
            # In this case, just pass an empty dictionary.
            pass

        # Everything went as expected, add dictionary
        # to the array.
        self.DICTIONARY['CLAUSES'] = clauses
        return 1

    def getSelectedColumnNames(self, query):
        columns = list()
        len_type = len(self.DICTIONARY['type'])

        # First check if the keyword "FROM" exists.
        # In this case, our indexing length would be
        # different - we will use WHERE.
        try:
            column_query = query[len_type:query.lower().index("from", len_type)]
        except ValueError:
            try:
                column_query = query[len_type:query.lower().index("where", len_type)]
            except ValueError:
                # This means there is no FROM and WHERE.
                # Which means, get entire query!
                column_query = query[len_type:]

        # Check basic syntax - ending with comma's,
        # Incomplete column names, etc.
        if self.checkSyntax(column_query, syntax_to_be_checked="select_column_names"):
            # Split the column names by comma.
            columns = column_query.strip(" ").split(",")

            # Make a new list of columns.
            self.DICTIONARY['columns'] = list()

            # Iterate through each column,
            # remove extra spaces, and also check
            # If column name is empty - raise error if True.
            for index in range(len(columns)):
                if len(columns[index]) == 0:
                    return self.clearAndMakeError("Incomplete SELECT Query.")
                self.DICTIONARY['columns'].append(columns[index].strip())

        # All went as expected, return with no error.
        return 1

    """
        Function to parse LOAD queries.
    """

    def parseLOADDatabase(self, query):
        spaced_query = query.lower().split(" ")

        # If there are only two words,
        # We assume it is "LOAD database".
        if len(spaced_query) == 2:
            self.DICTIONARY['database'] = query.lower()[len("LOAD"):].strip(" ")
            try:
                idex = self.DICTIONARY['database'].index("/", 0)
                return self.clearAndMakeError("No need to specify file name for just LOAD database.")
            except ValueError:
                return 1

        else:
            # Get the database name.
            self.DICTIONARY['database'] = query.lower()[len("LOAD"):query.lower().index("/")].strip(" ")
            # Get the CSV file name.
            self.DICTIONARY['csv_file_name'] = query.lower()[query.lower().index("/") + 1:query.lower().index(" as")].strip(" ")

            # Get the columns array string
            # within the brackets.
            column_array_string = query.lower()[query.lower().index(" as ", 0) + 4:].strip("(").strip(")")
            columns_array = column_array_string.split(",")

            # This is the columns array that will
            # get added to the DICTIONARY.
            columns = list()
            for index in range(len(columns_array)):
                # Strip the sentence of any extra spaces.
                columns_array[index] = columns_array[index].strip(" ")

                # Throw error if anything is empty.
                if columns_array[index] == "":
                    return self.checkSyntax("Incorrect syntax.")

                # Extract key:value pair.
                column_string = columns_array[index].split(":")

                # Loop through each such pair array.
                for second_index in range(len(column_string)):
                    # Strip all spaces.
                    # Ex => key:pair vs key: pair, etc
                    column_string[second_index] = column_string[second_index].strip(" ")

                    # Throw error if anything is empty.
                    if column_string[second_index] == "":
                        return self.checkSyntax("Incorrect syntax.")

                # Make a columnn dictionary.
                column = dict()

                # Add name, and datatype for that column.
                column['name'] = column_string[0]
                column['datatype'] = column_string[1]

                # Append this column to the columns array.
                columns.append(column)

            # All went well, insert into main dictionary.
            self.DICTIONARY['column_types'] = columns
