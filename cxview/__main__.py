import os, sys

sys.path.append(os.getcwd())

from cxview import CxView

app = CxView().create()

app.use('basic')

app.show_channel('basic')

app.run()
