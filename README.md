PyNetMap est un logiciel qui vise à simplifier la vie aux administrateurs systèmes.
Lorsque vous gérez une infrastructure de plusieurs serveurs, éventuellement des machines virtuelles et des conteneurs. Il devient difficile de retrouver le chemin pour vous connecter en SSH sur vos machines


# Pourquoi ?

Quand je suis arrivé chez DotRiver dans le cadre de mon stage de fin de licence en 2018, J’ai dû identifier toute l’infrastructure de DotRiver manuellement, consulter la documentation qui parfois n’était pas à jour pendant des heures pour pouvoir m’y retrouver.

Même après avoir tout noté, ça me prenait plusieurs minutes parfois pour trouver quel chemin (rebond SSH) pour pouvoir accéder à une VM.

J’ai donc entamé le développement d’un outil qui me permettait de générer ces chemins-là facilement en un clic.

Je me suis vite rendu compte que ce pouvait être plus puissant que ça. En effet le seul fait de savoir accéder à n’importe quelle machine, était déjà une base solide pour aller plus loin.
J’ai donc imaginé un système qui pouvait détecter les machines virtuelles automatiquement et les ajouter à la base ainsi que le fait d’exécuter régulièrement des commandes sur les différentes machines.
L’outil devenait de plus en plus intéressent, j’ai donc décidé de le publier.

# Qu’est-ce que ça permet de faire ?

## Cartographie
À la base cet outil servait principalement à cartographier une infrastructure et nettement grâce à l’outil Graphviz, histoire de voir rapidement quel VM est dans quel serveur et quel serveur est dans quelle infrastructure rattachée à quel client.
Donc en deux mots, PyNeyMap est d’abord un outil de cartographie.

## Gestionnaire de connexions SSH
Ensuite le fait d’avoir cette arborescence, m’a permis d’implémenter la connexion SSH sur les VM, même si celle-ci est dans un réseau local interne au serveur. Il suffit d’avoir une seule machine qui servira de proxy SSH pour accéder à toutes les autres.

Grâce à ce système, il suffit de paramétrer le pont SSH sur PyNetMap et vous cliquez une VM pour ouvrier une console dessus en SSH

## Outil de monitoring
PyNetMap prend en charge l’API Zabbix et Proxmox pour récupérer régulièrement des informations de monitoring des différentes VM/PM, 
Les informations récupérées sont :
- Utilisation CPU
- Utilisation RAM
- Ratio Espace Libre / Capacité disque
- Ratio Espace Libre / Capacité des points de montages
- Uptime

## Outil de découverte réseau
Connaissant la nature d’un serveur lambda, un module permet de découvrir ce qui tourne sur ce serveur, si par exemple vous ajoutez un serveur Proxmox dans PyNetMap, ce dernier va lancer à chaque cycle la découverte des VM, conteneurs qui tourne dessus et les ajoute à la base.
cette découverte concerne :
- L'adresse IP de la VM
- Son adresse MAC
- Son nom
- Son ID Proxmox

les informations complémentaires doivent être rajoutées manuellement.

# Fonctionnalités :
- Cartographier arborescence des Serveurs/VM
- Recherche par mots clé, adresse IP, nom ....
- Établir un pont VPN via SSH (sshuttle pour les intimes)
- Exporter un fichier .md de description de toutes les machines 
- Gestion d’utilisateur avec plusieurs droits ( Édition , Accès terminal, Gestion d’utilisateurs)
- Ouverture de console SSH sur une machine en : 
	- Externe via votre terminal favori
	- Interne, attachée à la fenêtre PyNetMAP



# Implémentations futures :
Je continue le développement régulièrement sur PyNetMap et je vise à implémenter d’autre fonctionnalité plus avancée nettement :
- Prise en charge des différentes clés SSH assignable aux utilisateurs et aux VM ce qui permettra une gestion plus approfondie des droits d’accès
- Un module OpenStack et un autre pour Docker ( Découverte et Monitoring comme sur Proxmox)
- Création et contrôle de VM directement depuis PyNetMAP ( OpenStack, Docker et Proxmox) et éventuellement déploiement de configuration/script automatisé (Ansible ?) 
- Intégration de découvert d’équipements réseau ( routeur, switch…etc.)
- Prise en charge de cluster Kubernetes.
	
Je reste ouvert à toute suggestion de fonctionnalités, et pour ceux d’entre vous qui souhaitent contribuer au projet, vous êtes les bienvenues.

**Lien de la page web**
https://www.equantum.fr/fr/apps/pynetmap
