# Tic-Tac-Toe (Jogo da Velha)

## XO³ - Jogo da Velha Multiplayer

XO³ é uma aplicação web completa para partidas de Jogo da Velha, com foco na comunicação em tempo real, gerenciamento de sessões de usuário e arquitetura de rede híbrida.

Ela foi desenvolvida em **Python com Flask**, utilizando **MongoDB Atlas** para armazenar as salas e partidas em tempo real.

O projeto permite que jogadores criem ou entrem em salas e joguem diretamente pelo navegador.

## Funcionalidades Implementadas

- **Autenticação de Usuário:** Sistema completo de registro (Sign Up) e login (Login).

- **Gerenciamento de Sessão:** Uso de JSON Web Tokens (JWT) para proteger rotas e gerenciar a sessão do usuário.

- **Modo Multiplayer (PvP) Online:** Jogue em tempo real contra outros usuários cadastrados.

- **Modo Single-Player (PvCPU):** Jogue offline contra um BOT (IA local) para treinar.

- **Lobby e Usuários Online:** Ao logar, o usuário entra em um lobby onde pode ver uma lista de todos os outros jogadores online no momento.

- **Sistema de Convites:** Capacidade de enviar um convite de jogo para qualquer usuário online e receber notificações de convite.

- **Salas de Jogo Privadas:** Ao aceitar um convite, os dois jogadores são movidos para uma sala de jogo privada.

- **Jogabilidade Sincronizada:** As jogadas são refletidas instantaneamente na tela do oponente usando WebSockets.

- **Sistema de Revanche:** Ao final da partida, os jogadores podem optar por "Jogar Novamente" sem precisar voltar ao lobby.

- **Página "About Us":** Uma página estática apresentando os desenvolvedores do projeto.

- **Ranking Global:** Uma página pública que exibe um placar com as estatísticas de vitórias, derrotas e empates de todos os jogadores.


## Tecnologias utilizadas

**Backend**
- Python
- Flask
- Flask-SocketIO
- PyJWT
- python-dotenv
- eventlet

**Banco de Dados**
- MongoDB Atlas
- PyMongo

**Frontend**
- HTML
- CSS
- JavaScript


## Como rodar o projeto localmente

### 1- Clonar o repositório
```
git clone https://github.com/lays-carvalho/tic-tac-toe.git
cd tic-tac-toe
```

### 2- Criar e ativar o ambiente virtual
```
python -m venv venv
```

### 3- Instalar as dependências
```
pip install -r requirements.txt
```


## Variáveis de ambiente

Crie um arquivo **.env** na raiz do projeto com o seguinte conteúdo:

```
MONGO_URI=mongodb+srv://USUARIO:SENHA@cluster.mongodb.net/tictactoe
SECRET_KEY=sua_chave_secreta
```

⚠️ Substitua USUARIO e SENHA pelas credenciais do usuário criado no MongoDB Atlas.



## ▶️ Executar a aplicação
```
python run.py
```

A aplicação ficará disponível em:
```
http://localhost:5000
```
⚠️ Caso a porta 5000 esteja em uso, a aplicação utilizará a porta definida na variável PORT.


## Observações
- O MongoDB Atlas é utilizado para manter o banco de dados online.

- O projeto possui um agendador automático que limpa salas inativas.

- Ideal para estudos de Flask, Socket.IO e integração com MongoDB.



## Status do projeto
- Funcional ✅
- Em constante melhoria 🛠️


## 🚀 Demo
A aplicação está disponível em:
👉 https://tic-tac-toe-l3z1.onrender.com


## Contato

- 📧 Email: lays.carvalho.dev@gmail.com  
- 💼 LinkedIn: https://www.linkedin.com/in/lays-cruz-carvalho/ 
- 💻 GitHub: https://github.com/lays-carvalho





