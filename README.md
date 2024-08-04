# zoozl

Server for chatbot services

## Usage

For basic example a chatbot plugin is provided in `zoozl.plugins` package. It is a simple chatbot that allows to play bulls & cows game. It is also a plugin that is loaded in case no configuration file is provided.

### Run websocket server

```bash
python -m zoozl 1601 --conf chatbot.toml
```
where `1601` is the port number and `chatbot.toml` is optional configuration file.

## Architecture

zoozl package contains modules that handle various input interfaces like websocket or http POST and a chatbot interface that must be extended by plugins. Without plugin zoozl is not able to respond to any input. Plugin can be considered as a single chat assistant to handle a specific task. Plugin can be huge and complex or simple and small. It is up to the developer to decide how to structure plugins.
![zoozl_package](docs/images/zoozl_package.svg)


## Plugin
TODO: Describe plugin interface and creation
TODO: Add authentication and authorization interaction between chatbot and plugin
