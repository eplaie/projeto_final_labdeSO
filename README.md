# Processador de Imagens com Kubernetes

Sistema de processamento de imagens escalável utilizando Threads para processamento paralelo, Docker para containerização e Kubernetes para orquestração e balanceamento de carga.

## Estrutura do Projeto
```
projeto/
├── src/
│   ├── templates/           # Templates da interface web
│   │   ├── base.html       # Template base
│   │   ├── index.html      # Página inicial
│   │   ├── status.html     # Página de status
│   │   └── dashboard.html  # Dashboard
│   ├── image_processor.py  # Processador de imagens com threads
│   └── api.py             # API REST
├── docker/
│   ├── Dockerfile.app     # Dockerfile para a aplicação
│   ├── Dockerfile.db      # Dockerfile para o PostgreSQL
│   └── init.sql          # Script de inicialização do banco
└── k8s/
    ├── deployment.yaml    # Configuração de deployment K8s
    ├── service.yaml      # Configuração de serviços K8s
    └── postgres.yaml     # Configuração do PostgreSQL
```

## Pré-requisitos

- Ubuntu/WSL2
- Docker
- Minikube
- kubectl
- Python 3.9+

## Instalação e Configuração

1. **Clone o repositório**:
```bash
git clone https://github.com/eplaie/projeto_final_labdeSO.git
cd projeto_final_labdeSO
```

### 2. Instalando Docker
```bash
# Atualizar pacotes
sudo apt-get update

# Instalar dependências no diretório raiz do projeto
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# Adicionar chave GPG do Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Adicionar repositório
echo \
  "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER

# Iniciar serviço
sudo service docker start
```

### 3. Instalando Minikube e kubectl
```bash
# Instalar Minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Instalar kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

## Configuração e Execução



1. **Inicie o Minikube**:
```bash
minikube start
```

2. **Configure o Docker para usar o Minikube**:
```bash
eval $(minikube docker-env)
```

3. **Construa as imagens Docker**:
```bash
# Construir imagem da aplicação
docker build -t image-processor:latest -f docker/Dockerfile.app .

# Construir imagem do PostgreSQL (importante usar este caminho)
docker build -t postgres-db:latest -f docker/Dockerfile.db docker/
```

4. **Criar secret para o PostgreSQL**:
```bash
kubectl create secret generic postgres-secret \
  --from-literal=username=postgres \
  --from-literal=password=postgres
```

5. **Aplicar as configurações do Kubernetes**:
```bash
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/deployment.yaml
```

6. **Verificar se tudo está rodando**:
```bash
kubectl get pods
kubectl get services
```

7. **Expor o serviço (mantenha este terminal aberto)**:
```bash
minikube service image-processor --url
```

## Usando o Sistema

1. Acesse a interface web usando a URL fornecida pelo comando minikube service
2. Use a interface para:
   - Upload de imagens
   - Monitoramento do processamento
   - Visualização de estatísticas no dashboard
   - Download das imagens processadas

No repositório foi deixado uma imagem para teste, com o formato .jpg.
Se preferir, pode testar com outras imagens em formato .jpg

## Monitoramento

Para verificar logs e status:
```bash
# Logs do processador de imagens
kubectl logs -f deployment/image-processor

# Logs do PostgreSQL
kubectl logs postgres-0

# Status dos pods
kubectl get pods

# Dados na tabela
kubectl exec -it postgres-0 -- psql -U postgres -d imagedb -c "SELECT id, status, length(original_data), length(processed_data) from processed_images ORDER BY uploaded_at DESC LIMIT 5;"
```

## Limpeza

Para parar o sistema:
```bash
kubectl delete -f k8s/
minikube stop
```

## Solução de Problemas

Um problema sem solução até o momento é o do formato de Download da imagem (contém um erro ao abrir a imagem), o objetivo do trabalho era redimensionar, por exemplo, se você enviar uma imagem de 2000x1500 pixels, ela será redimensionada para 800x600 (mantendo a proporção)
se você enviar uma imagem de 600x400 pixels, ela permanecerá com esse tamanho

1. **Erro de permissão no Docker**:
```bash
sudo chmod 666 /var/run/docker.sock
```

2. **Pods não iniciam**:
```bash
kubectl describe pod [nome-do-pod]
```

3. **Erro no port-forward**:
Reinicie o serviço com:
```bash
minikube service image-processor --url
```

4. **Erro de conexão com banco**:
Verifique se o pod do PostgreSQL está rodando:
```bash
kubectl get pods | grep postgres
```
