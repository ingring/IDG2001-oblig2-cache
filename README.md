# Vcard parser

## About the project
This is a vcard parser with seperate client, main api and a cache. The users can either upload their contacts in a vcard formated file or download it as a vcard file. The contact information is stored in a MongoDB database as JSON format.

## Seperated repos
To seperate the project we have craeted three different GitHub repositories for easily hosting them on different platforms. 
- MAIN API: https://github.com/ingring/IDG2001-oblig2-api
- CLIENT: https://github.com/ingring/IDG2001-oblig2-client
- CACHE: https://github.com/ingring/IDG2001-oblig2-cache

## Technology
- MAIN API: Python with Flask as framework. It connects to a MongoDB database. 
- CLIENT: Vanilla JavaScript with HTML and CSS.
- CACHE: Python with Flask as framework. Uses redis as the cache database. 

## Hosting
One of the projects requirements was to explore and host on different platforms. We hosted on Railway and Render. Since Railway isn't completely free we aren't hosting in this moment. 

## How to use
- Install Python requirements `pip install -r requirements.txt`
- Start the server for development `python3 main.py`
