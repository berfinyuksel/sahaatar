import sys

sys.dont_write_bytecode = True
from website import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True,port = 5002)