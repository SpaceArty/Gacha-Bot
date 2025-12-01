
def C001(carte): # Template

    return

def C002(carte): # Template
    return

# Un dictionnaire pour gérer les passifs par ID
passifs = {
    'C001': C001,
    'C002': C002
}

# Fonction pour appliquer un passif
def appliquer_passif(carte):
    passif = carte.get('passif')
    if passif in passifs:
        return passifs[passif](carte)
    return carte