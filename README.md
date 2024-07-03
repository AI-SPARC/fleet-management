# Fleet Management System 🚘

<img align="left" width="150" height="150" src="./img/fleet-manager-icon.png">

### A master control for automated guided vehicles(AGVs) following the VDA-5050 standard.
Write something here... 

Write something here... 

Write something here... 



## 🛠 Prerequisites

Before you begin, make sure you have installed the following tools:

- [Miniconda](https://docs.anaconda.com/free/miniconda/) (24.4.0)
- [NodeJS (Optional)](https://nodejs.org/en/download/package-manager/current) (22.3.0)

## ⚙ Installing

To install the application, follow these steps:

1. Create an virtual enviroment using conda and activate it:
```
conda create --name fleet_management python=3.11.9
conda activate fleet_management
```

2. Install the dependecies with pip:
```
pip install -r .\requirements.txt
```

3. Populate the .env with the Discord Token:
```
BROKER_ADDRESS=write your broker address here
BROKER_PORT=write your broker port here
```

## 🚀 Running

To start the server you just need to execute the main.py file, like this:

```
python main.py
```
* You can acess the landing page at:
```
http://localhost:3000/
```

* The API docs is at:
```
http://localhost:3000/docs
```

* And the MQTT messages docs is at:
```
http://localhost:3000/mqtt
```

## 🤩 Collaborators

We thank the following people who contributed to this project:

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/vannisson" title="Vannisson Github Profile">
        <img src="https://github.com/vannisson.png" width="100px;" alt="Geovane Github Profile Photo"/><br>
        <sub>
          <b>Geovane Filho</b>
        </sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/becacoli" title="Becacoli Github Profile">
        <img src="https://github.com/becacoli.png" width="100px;" alt="Becacoli Github Profile Photo"/><br>
        <sub>
          <b>Rebeca Queiroz</b>
        </sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/glauberrleite" title="GlauberRLeite Github Profile">
        <img src="https://github.com/glauberrleite.png" width="100px;" alt="Glauber Github Profile Photo"/><br>
        <sub>
          <b>Glauber Leite</b>
        </sub>
      </a>
    </td>
  </tr>
</table>

## 📜 License

Esse projeto está sob licença. Veja o arquivo [LICENÇA](LICENSE.md) para mais detalhes.

## 📚 References

* [VDA-5050](https://github.com/VDA5050/VDA5050)
* Add more references...