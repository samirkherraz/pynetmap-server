# PyNetMAP
PyNetMap est un logiciel qui vise à simplifier la vie aux administrateurs systèmes.
Lorsque vous gérez une infrastructure de plusieurs serveurs, éventuellement des machines virtuelles et des conteneurs. il devient difficile de retrouver le chemin pour vous connecter en SSH sur vos machines

## Pourquoi

Quand je suis arrivé chez DotRiver dans le cadre de mon stage de fin de licence en 2018, J'ai dû identifier toute l'infrastructure de DotRiver manuellement, consulter la documentation qui parfois n'était pas à jour pendant des heures pour pouvoir m'y retrouver.

Même après avoir tout noté, ça me prenait plusieurs minutes parfois pour trouver quel chemin ( rebond SSH) pour pouvoir accéder à une VM.

J'ai donc entamé le développement d'un outil qui me permettait de générer ces chemins-là facilement en un clique.

je me suis vite rendu compte que ce pouvait être plus puissant que ça. en effet le seul fait de savoir accéder à n'importe quelle machine, était déjà une base solide pour aller plus loin.
J'ai donc imaginé un système qui pouvait détecter les machines virtuelles automatiquement et les ajouter à la base ainsi que le fait d'exécuter régulièrement des commandes sur les différentes machines afin d'avoir en plus un outil de monitoring.
L'outil devenait de plus en plus intéressent, j'ai donc décidé de le publier.

## Qu'est-ce que ça permet de faire ?

### Cartographie 
À la base cet outil servait principalement à cartographier une infrastructure et nettement grace à l'outil Graphviz, histoire de voir rapidement quel vm est dans quel serveur et quel serveur est dans quelle infrastructure rattachée à quel client.
Donc en deux mots, PyNeyMap est d'abord un outil de cartographie.


### Gestionaire de connection ssh
Ensuite le fait d'avoir cette arborescence, m'a permis d'implémenter la connexion SSH sur les VM, même si celle-ci est dans un réseau local interne au seveur. il suffit d'avoir une seule machine qui servira de proxy ssh pour accéder à toutes les autres.

Grâce à ce système, il suffit de paramétrer le pont SSH sur PyNetMap et vous cliquez sur n'importe quel VM pour ouvrier une console dessus en SSH

### Outil de monitoring
Une fois le gestionnaire de connexion ssh implémenté, c'est dommage de rien en faire.
un Daemon est donc lancé afin d'exécuter des commandes régulièrement sur les machines afin de récupérer quelques informations :
	- L'utilisation RAM
	- L'utilisation CPU 
	- Le nombre de coeurs
	- L'utilisation des disques 
	- Les points de montage et leurs utilisations 
	- Les services qui écoutent sur le réseau 
	- L'adresse Mac 
	- L'adresse IP

Une fois ces informations sont récupérées, un algorithme se lance pour vérifier que tout va bien. si jamais une erreur ou une anomalie est détectée, une alerte est alors générée pour prévenir qu'il y a un problème. ( comme sur n'importe quel outil de monitoring : Zabbix )

 
### Outil de découverte réseau
Connaissant la nature d'un serveur lambda, un module permet de découvrir ce qui tourne sur ce serveur, si par exemple vous ajoutez un serveur Proxmox dans PyNetMap, ce dernier va lancer à chaque cycle la découverte des vm, conteneurs qui tourne dessus et les ajoute à la base.
cette decouverte concerne :
	- L'adresse ip de la vm
	- Son adresse mac
	- Son nom

les informations complémentaires doivent être rajoutées manuellement.

## Aujourd'hui :
Le système de monitoring ne prend en charge que Linux ( installation des dépendances automatiques pour les distributions Debian bases)
Sinon pour les autres distributions les outils suivants sont requis pour le monitoring :
	- arp-scan
	- route
	- sockstat
	- vmstat

Mais aussi monitoring des VM et conteneurs via l'api de Proxmox 

La découverte est prise en charge que pour proxmox via l'api.

## Implémentation future :
Je continue le développement régulièrement sur PyNetMap et je vise à implémenter d'autre fonctionnalité plus avancée nettement :
	- Un module OpenStack et un autre pour Docker ( Découverte et Monitoring comme sur proxmox )
	- Création et contrôle de VM directement depuis PyNetMAP ( OpenStack, Docker et Proxmox ) et éventuellement déployment de configuration/script automatisé ( Ansible ? ) 
	- Intégration de découvert d'equiements réseau ( routeur, switch...etc.)
	- Implémentation d'un module de monitoring via SNMP
	
Je reste ouvert à toute suggestion de fonctionnalités, et pour ceux d'entre vous qui souhaite contribuer au projet, tout le monde est le bienvenue.
