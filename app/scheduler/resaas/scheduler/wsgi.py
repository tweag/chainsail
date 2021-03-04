"""Web Server Gateway Interface"""

####################
# FOR PRODUCTION
####################
from resaas.scheduler.app import app
from resaas.scheduler.core import db

if __name__ == "__main__":
    ####################
    # FOR DEVELOPMENT
    ####################
    db.create_all()
    app.run(host="0.0.0.0", debug=True)
