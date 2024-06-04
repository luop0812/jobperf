''' block_parser.py '''

"""
This class provides methods to process text files with a simple "block" format.
The leading line of each block starts with a non-empty character.
Other lines within the same block starts with one or more empty characters.
"""

class BlockParser:

    def __init__(self, filename="", keys=[]):
        self._filename = filename
        self._keys = keys
        self._output_list = []
           
    """
    input: a simple block
    output: a list of strings "key=value"
    """
    def _process(self, block):
        mylist = []
        for line in block:
            tokens = line.split()
            for token in tokens:
                token_split = token.split("=")
                key = token_split[0]
                if key in self._keys:
                    mylist.append(token)
        return mylist

    """
    input: a text file with a number of simple blocks
    output: a list of lists.
    """
    def _process_blocks(self):

        with open(self._filename, "r") as fp:

            flush = True
            block = []

            for line in fp:
                if not line[0].isspace():
                    mylist = self._process(block)
                    if len(mylist):
                        self._output_list.append(mylist)

                    block = [] 
                    flush = False

                if flush:
                    continue

                block.append(line)

            # process the last block
            mylist = self._process(block)
            if len(mylist):
                self._output_list.append(mylist)

        return self._output_list

    def get_processed_blocks(self):
        return self._process_blocks()


## test
#keys = ["JobId", "UserId", "Nodes", "GRES"]
#block_parser = BlockParser("test.txt", keys)
#block_list = block_parser.get_processed_blocks()
#print(block_list)
