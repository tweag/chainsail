"""Web Server Gateway Interface"""

####################
# FOR PRODUCTION
####################
from chainsail.mcmc_stats_server.app import app

if __name__ == "__main__":
    ####################
    # FOR DEVELOPMENT
    ####################
    app.run(host="0.0.0.0", debug=True)
