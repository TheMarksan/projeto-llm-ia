# Recomendação de Vinhos com IA

Este projeto utiliza inteligência artificial para recomendar vinhos harmonizados com pratos da culinária brasileira e internacional. A aplicação é construída em Python, usando Streamlit para interface web, Google Generative AI para sugestões inteligentes, e pandas para manipulação de dados.

## Funcionalidades
- Interface web interativa para seleção de pratos
- Sugestão de vinhos harmonizados baseada em IA
- Base de dados de pratos (`pratos.json`) com categorias, ingredientes e sugestões de harmonização
- Visualização de informações detalhadas sobre pratos e vinhos

## Estrutura dos Dados
O arquivo `pratos.json` contém uma lista de pratos com os seguintes campos:
- `nome`: Nome do prato
- `descricao`: Descrição detalhada
- `categoria`: Tipo (carnes, aves, peixes, massas, vegetariano, queijos, sobremesas, etc.)
- `ingredientes`: Lista de ingredientes principais
- `intensidade`: Intensidade de sabor (leve, média, forte, doce)
- `harmonizacao_sugerida`: Lista de estilos de vinho recomendados

## Como Executar
1. **Clone o repositório:**
   ```bash
   git clone <url-do-repositorio>
   cd recomendacao-vinho-ia
   ```
2. **Crie e ative o ambiente virtual:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   # ou
   pip install streamlit google-generativeai pandas
   ```
4. **Execute a aplicação:**
   ```bash
   streamlit run app.py
   ```

## Dependências
- Python 3.12+
- streamlit
- google-generativeai
- pandas

## Personalização
- Para adicionar ou editar pratos, modifique o arquivo `pratos.json`.
- Para alterar regras de harmonização, ajuste a lógica no código Python (normalmente em `app.py`).

## Sugestão de Uso
- Escolha um prato na interface web
- Veja as sugestões de vinhos harmonizados
- Explore detalhes sobre ingredientes e estilos de vinho

## Licença
Este projeto é distribuído sob a licença MIT.


---

Se tiver dúvidas ou sugestões, abra uma issue ou envie um pull request!
