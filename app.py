import streamlit as st
import json
import pandas as pd
import google.generativeai as genai
import re
from collections import Counter

# CONFIGURAÇÃO DA API DO LLM
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except (st.errors.StreamlitSecretNotFoundError, KeyError):
    api_key = "AIzaSyDDNFG3dhpyVlIgMTvd43DmEodrVQtYUcY"
    st.warning("⚠️ Usando chave de API em modo desenvolvimento")

genai.configure(api_key=api_key)

# --- CATEGORIAS E PALAVRAS-CHAVE AVANÇADAS ---

CATEGORIAS_PRATO = {
    "carnes_vermelhas": {
        "palavras_chave": ["bife", "picanha", "contrafilé", "alcatra", "costela", "carne bovina", "boi", "carne de porco", "porco", "lombo", "carneiro", "cordero", "vitela"],
        "intensidade": "forte"
    },
    "aves": {
        "palavras_chave": ["frango", "galinha", "peru", "chester", "pato", "codorna", "ave", "peito de frango", "coxa", "sobrecoxa"],
        "intensidade": "media"
    },
    "peixes": {
        "palavras_chave": ["salmão", "truta", "bacalhau", "atum", "tilápia", "pescada", "robalo", "dourado", "corvina", "peixe", "file de peixe"],
        "intensidade": "leve"
    },
    "frutos_mar": {
        "palavras_chave": ["camarão", "lagosta", "siri", "caranguejo", "ostra", "mexilhão", "polvo", "lula", "marisco", "fruto do mar"],
        "intensidade": "leve"
    },
    "massas": {
        "palavras_chave": ["macarrão", "espaguete", "talharim", "ravioli", "lasanha", "nhoque", "canelone", "massa", "carbonara"],
        "intensidade": "media"
    },
    "queijos": {
        "palavras_chave": ["queijo", "brie", "gorgonzola", "cheddar", "mussarela", "parmesão", "provolone", "coalho", "minas"],
        "intensidade": "media"
    },
    "vegetariano": {
        "palavras_chave": ["legumes", "vegetais", "salada", "berinjela", "abobrinha", "cogumelo", "tofu", "grão de bico", "lentilha", "vegetariano", "vegano"],
        "intensidade": "leve"
    },
    "sobremesas": {
        "palavras_chave": ["chocolate", "doce", "sobremesa", "pudim", "mousse", "sorvete", "torta", "bolo", "creme", "açúcar"],
        "intensidade": "doce"
    }
}

MÉTODOS_PREPARO = {
    "grelhado": ["grelhado", "grelhada", "na chapa", "churrasco", "assado na grelha"],
    "assado": ["assado", "assada", "forno", "roast"],
    "frito": ["frito", "frita", "empanado", "empanada", "dorê"],
    "cozido": ["cozido", "cozida", "estufado", "ensopado", "guisado"],
    "cru": ["cru", "crua", "tártaro", "sashimi", "ceviche"],
    "molho": ["molho", "sauce", "caldo", "ao molho"]
}

# --- FUNÇÕES PARA CARREGAR DADOS DOS JSONs ---

def carregar_vinhos():
    """Carrega a base de dados de vinhos do arquivo JSON."""
    try:
        with open('vinhos.json', 'r', encoding='utf-8') as f:
            dados = json.load(f)
            st.success(f"✅ Base de vinhos carregada: {len(dados)} vinhos encontrados")
            
            # Valida e corrige campos ausentes
            dados_validados = validar_dados_vinhos(dados)
            return dados_validados
            
    except FileNotFoundError:
        st.error("❌ Arquivo vinhos.json não encontrado!")
        st.info("📝 Criando arquivo vinhos.json com dados de exemplo...")
        return criar_arquivo_vinhos_exemplo()
    except json.JSONDecodeError as e:
        st.error(f"❌ Erro ao ler o arquivo vinhos.json: {e}")
        return []

def carregar_pratos():
    """Carrega a base de dados de pratos do arquivo JSON."""
    try:
        with open('pratos.json', 'r', encoding='utf-8') as f:
            dados = json.load(f)
            st.success(f"✅ Base de pratos carregada: {len(dados)} pratos encontrados")
            return dados
            
    except FileNotFoundError:
        st.error("❌ Arquivo pratos.json não encontrado!")
        st.info("📝 Criando arquivo pratos.json com dados de exemplo...")
        return criar_arquivo_pratos_exemplo()
    except json.JSONDecodeError as e:
        st.error(f"❌ Erro ao ler o arquivo pratos.json: {e}")
        return []

def validar_dados_vinhos(dados):
    """Valida e corrige campos ausentes nos dados dos vinhos."""
    for vinho in dados:
        # Garante que campos essenciais existam
        vinho.setdefault('perfil', 'equilibrado')
        vinho.setdefault('intensidade', 'media')
        vinho.setdefault('harmoniza_com', [])
        vinho.setdefault('notas', [])
        
        # Define perfil baseado no tipo se não especificado
        if vinho['perfil'] == 'equilibrado':
            if vinho['tipo'].lower() in ['tinto', 'red']:
                vinho['perfil'] = 'encorpado'
            elif vinho['tipo'].lower() in ['branco', 'white']:
                vinho['perfil'] = 'leve'
            elif vinho['tipo'].lower() in ['espumante', 'champagne']:
                vinho['perfil'] = 'leve'
                
        # Define intensidade baseada no perfil se não especificada
        if vinho['intensidade'] == 'media':
            if vinho['perfil'] == 'encorpado':
                vinho['intensidade'] = 'forte'
            elif vinho['perfil'] == 'leve':
                vinho['intensidade'] = 'leve'
    
    return dados

def criar_arquivo_vinhos_exemplo():
    """Cria um arquivo JSON de vinhos exemplo se não existir."""
    dados_exemplo = [
        {
            "nome": "Cabernet Sauvignon",
            "tipo": "Tinto",
            "notas": ["cassis", "cereja", "baunilha", "tabaco"],
            "harmoniza_com": ["carnes vermelhas", "queijos curados", "massas com molho vermelho"],
            "perfil": "encorpado",
            "intensidade": "forte"
        },
        {
            "nome": "Chardonnay",
            "tipo": "Branco", 
            "notas": ["maçã verde", "baunilha", "manteiga", "carvalho"],
            "harmoniza_com": ["frango", "peixes", "camarão", "massas brancas"],
            "perfil": "cremoso",
            "intensidade": "media"
        }
    ]
    
    try:
        with open('vinhos.json', 'w', encoding='utf-8') as f:
            json.dump(dados_exemplo, f, ensure_ascii=False, indent=2)
        st.success("✅ Arquivo vinhos.json criado com dados de exemplo!")
        return dados_exemplo
    except Exception as e:
        st.error(f"❌ Erro ao criar arquivo: {e}")
        return dados_exemplo

def criar_arquivo_pratos_exemplo():
    """Cria um arquivo JSON de pratos exemplo se não existir."""
    dados_exemplo = [
        {
            "nome": "Picanha na Chapa",
            "descricao": "Picanha grelhada na chapa com alho e sal grosso",
            "categoria": "carnes_vermelhas",
            "ingredientes": ["picanha", "alho", "sal grosso", "azeite"],
            "intensidade": "forte",
            "harmonizacao_sugerida": ["vinhos tintos encorpados", "malbec", "cabernet sauvignon"]
        },
        {
            "nome": "Salmão Grelhado",
            "descricao": "Salmão grelhado com molho de maracujá e arroz de açafrão",
            "categoria": "peixes",
            "ingredientes": ["salmão", "maracujá", "açafrão", "arroz"],
            "intensidade": "leve",
            "harmonizacao_sugerida": ["vinhos brancos", "sauvignon blanc", "pinot noir"]
        },
        {
            "nome": "Lasanha à Bolonhesa",
            "descricao": "Lasanha tradicional com molho bolonhesa e queijos",
            "categoria": "massas",
            "ingredientes": ["carne moída", "molho de tomate", "massa de lasanha", "queijo"],
            "intensidade": "media",
            "harmonizacao_sugerida": ["vinhos tintos médios", "chardonnay", "merlot"]
        },
        {
            "nome": "Risoto de Cogumelos",
            "descricao": "Risoto cremoso com cogumelos frescos e parmesão",
            "categoria": "vegetariano",
            "ingredientes": ["arroz arbório", "cogumelos", "parmesão", "vinho branco"],
            "intensidade": "media",
            "harmonizacao_sugerida": ["pinot noir", "chardonnay", "vinhos brancos leves"]
        }
    ]
    
    try:
        with open('pratos.json', 'w', encoding='utf-8') as f:
            json.dump(dados_exemplo, f, ensure_ascii=False, indent=2)
        st.success("✅ Arquivo pratos.json criado com dados de exemplo!")
        return dados_exemplo
    except Exception as e:
        st.error(f"❌ Erro ao criar arquivo: {e}")
        return dados_exemplo

# --- FUNÇÕES AVANÇADAS DE ANÁLISE ---

def buscar_prato_por_nome(nome_prato, dados_pratos):
    """Busca um prato pelo nome na base de dados."""
    nome_prato_lower = nome_prato.lower()
    
    for prato in dados_pratos:
        if nome_prato_lower in prato['nome'].lower():
            return prato
    
    # Se não encontrou exato, busca por similaridade
    for prato in dados_pratos:
        if any(palavra in nome_prato_lower for palavra in prato['nome'].lower().split()):
            return prato
    
    return None

def extrair_palavras_chave(descricao_prato):
    """Extrai palavras-chave e categorias da descrição do prato."""
    descricao = descricao_prato.lower()
    
    categorias_encontradas = []
    metodos_preparo = []
    ingredientes_especificos = []
    
    # Analisa categorias principais
    for categoria, info in CATEGORIAS_PRATO.items():
        for palavra in info["palavras_chave"]:
            if palavra.lower() in descricao:
                categorias_encontradas.append({
                    "categoria": categoria,
                    "intensidade": info["intensidade"],
                    "palavra_chave": palavra
                })
                break
    
    # Analisa métodos de preparo
    for metodo, palavras in MÉTODOS_PREPARO.items():
        for palavra in palavras:
            if palavra.lower() in descricao:
                metodos_preparo.append(metodo)
                break
    
    # Extrai ingredientes específicos usando regex
    ingredientes_comuns = ["alho", "cebola", "tomate", "limão", "azeite", "manteiga", 
                          "creme de leite", "vinho", "ervas", "tempero", "pimenta", "sal"]
    
    for ingrediente in ingredientes_comuns:
        if ingrediente in descricao:
            ingredientes_especificos.append(ingrediente)
    
    return {
        "categorias": categorias_encontradas,
        "metodos_preparo": metodos_preparo,
        "ingredientes_especificos": ingredientes_especificos,
        "texto_original": descricao_prato
    }

def analisar_perfil_sabor(analise):
    """Analisa o perfil de sabor baseado nas categorias e métodos."""
    if not analise["categorias"]:
        return "equilibrado"
    
    # Determina perfil baseado na categoria principal
    categorias_por_prioridade = ["sobremesas", "carnes_vermelhas", "queijos", "aves", "frutos_mar", "peixes", "massas", "vegetariano"]
    
    for categoria in categorias_por_prioridade:
        if any(cat["categoria"] == categoria for cat in analise["categorias"]):
            categoria_principal = categoria
            break
    else:
        categoria_principal = analise["categorias"][0]["categoria"]
    
    # Mapeia categoria para perfil de sabor
    perfis = {
        "carnes_vermelhas": "encorpado",
        "aves": "medio",
        "peixes": "leve",
        "frutos_mar": "leve",
        "massas": "medio", 
        "queijos": "cremoso",
        "vegetariano": "fresco",
        "sobremesas": "doce"
    }
    
    return perfis.get(categoria_principal, "equilibrado")

def recomendacao_inteligente(prato_encontrado, analise_prato, dados_vinhos):
    """Recomendação avançada baseada no prato encontrado e análise."""
    
    # Lista para armazenar vinhos com seus scores
    vinho_com_scores = []
    
    for vinho in dados_vinhos:
        score = 0
        
        # Se encontrou o prato na base, usa as harmonizações sugeridas
        if prato_encontrado and 'harmonizacao_sugerida' in prato_encontrado:
            for sugestao in prato_encontrado['harmonizacao_sugerida']:
                sugestao_lower = sugestao.lower()
                # Verifica se o vinho está nas sugestões
                if any(termo in sugestao_lower for termo in [vinho['nome'].lower(), vinho['tipo'].lower()]):
                    score += 5
                # Verifica correspondência por perfil
                elif any(termo in sugestao_lower for termo in [vinho.get('perfil', ''), vinho.get('intensidade', '')]):
                    score += 3
        
        # Score por categoria correspondente
        categorias = [cat["categoria"] for cat in analise_prato["categorias"]]
        for harmonizacao in vinho.get('harmoniza_com', []):
            harmonizacao_lower = harmonizacao.lower()
            
            # Verifica correspondência direta com categorias
            for categoria in categorias:
                if categoria.replace('_', ' ') in harmonizacao_lower:
                    score += 3
            
            # Verifica correspondência com palavras-chave específicas
            for cat_info in analise_prato["categorias"]:
                if cat_info["palavra_chave"] in harmonizacao_lower:
                    score += 2
        
        # Score por intensidade correspondente
        intensidade_prato = analise_prato["categorias"][0]["intensidade"] if analise_prato["categorias"] else "media"
        intensidade_vinho = vinho.get('intensidade', 'media')
        
        if intensidade_prato == intensidade_vinho:
            score += 2
        elif (intensidade_prato == "forte" and intensidade_vinho == "media") or \
             (intensidade_prato == "leve" and intensidade_vinho == "media"):
            score += 1
        
        # Score por perfil de sabor
        perfil_sabor = analisar_perfil_sabor(analise_prato)
        perfil_vinho = vinho.get('perfil', 'equilibrado')
        if perfil_sabor == perfil_vinho:
            score += 2
        
        if score > 0:
            vinho_com_scores.append({
                "vinho": vinho,
                "score": score
            })
    
    # Ordena por score (decrescente)
    vinho_com_scores.sort(key=lambda x: x["score"], reverse=True)
    
    # Retorna apenas os vinhos (sem os scores)
    recomendados_ordenados = [item["vinho"] for item in vinho_com_scores[:3]]  # Top 3
    
    return recomendados_ordenados

def gerar_justificativa_avancada(prato_encontrado, analise_prato, vinho_escolhido):
    """Gera justificativa avançada usando LLM com contexto detalhado."""
    try:
        model = genai.GenerativeModel('gemini-pro')
        
        contexto_prato = f"""
        Prato encontrado na base: {prato_encontrado['nome'] if prato_encontrado else 'Não encontrado'}
        Descrição: {prato_encontrado['descricao'] if prato_encontrado else analise_prato['texto_original']}
        Categoria: {prato_encontrado['categoria'] if prato_encontrado else 'Não especificada'}
        """
        
        contexto_analise = f"""
        Análise do prato:
        - Categorias identificadas: {[cat['categoria'] for cat in analise_prato['categorias']]}
        - Métodos de preparo: {analise_prato['metodos_preparo']}
        - Perfil de sabor: {analisar_perfil_sabor(analise_prato)}
        """
        
        prompt = f"""
        Atue como um sommelier experiente analisando esta harmonização:
        
        {contexto_prato}
        {contexto_analise}
        
        VINHO RECOMENDADO: {vinho_escolhido['nome']} ({vinho_escolhido['tipo']})
        Perfil: {vinho_escolhido.get('perfil', 'Não especificado')}
        Notas: {', '.join(vinho_escolhido.get('notas', []))}
        
        Explique em 3-4 linhas por que essa harmonização funciona considerando:
        - Correspondência de intensidades
        - Complementaridade de sabores
        - Como o vinho interage com os ingredientes e método de preparo
        
        Seja técnico porém acessível.
        """
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        # Fallback avançado
        categorias = [cat['categoria'] for cat in analise_prato['categorias']]
        fallback = f"Esta harmonização entre {categorias[0] if categorias else 'o prato'} e o {vinho_escolhido['tipo']} funciona devido à complementaridade de intensidades e sabores."
        return f"💡 **Análise do Sommelier:** {fallback}"

# --- INTERFACE DO USUÁRIO ---

st.set_page_config(page_title="Sommelier AI Avançado", page_icon="🍷", layout="wide")

st.title("🍷 Sommelier AI Avançado")
st.markdown("Descreva seu prato para receber recomendações de vinho baseadas na nossa base de dados")

# Carregar dados dos JSONs
dados_vinhos = carregar_vinhos()
dados_pratos = carregar_pratos()

# Entrada do usuário com sugestões de pratos
nomes_pratos = [prato['nome'] for prato in dados_pratos]
prato_selecionado = st.selectbox(
    "Selecione um prato ou digite o nome:",
    options=[""] + nomes_pratos,
    help="Selecione um prato da lista ou digite o nome manualmente"
)

prato_input_custom = st.text_input(
    "Ou descreva seu prato manualmente:",
    placeholder="Ex: Salmão grelhado com molho de limão...",
    disabled=bool(prato_selecionado)
)

# Usa o prato selecionado ou o input customizado
prato_para_buscar = prato_selecionado if prato_selecionado else prato_input_custom

if st.button("🎯 Buscar Harmonizações", type="primary"):
    if prato_para_buscar:
        st.write("---")
        
        # Busca o prato na base de dados
        with st.spinner('🔍 Procurando prato na base de dados...'):
            prato_encontrado = buscar_prato_por_nome(prato_para_buscar, dados_pratos)
        
        # Análise avançada do prato
        with st.spinner('🔍 Analisando descrição do prato...'):
            if prato_encontrado:
                analise_prato = extrair_palavras_chave(prato_encontrado['descricao'])
            else:
                analise_prato = extrair_palavras_chave(prato_para_buscar)
        
        # Mostra informações do prato
        st.subheader("📊 Informações do Prato")
        
        if prato_encontrado:
            st.success(f"✅ Prato encontrado na base: **{prato_encontrado['nome']}**")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Descrição:** {prato_encontrado['descricao']}")
                st.write(f"**Categoria:** {prato_encontrado.get('categoria', 'Não especificada').replace('_', ' ').title()}")
                st.write(f"**Intensidade:** {prato_encontrado.get('intensidade', 'Média').title()}")
            
            with col2:
                st.write(f"**Ingredientes:** {', '.join(prato_encontrado.get('ingredientes', []))}")
                if prato_encontrado.get('harmonizacao_sugerida'):
                    st.write(f"**Harmonizações sugeridas:** {', '.join(prato_encontrado['harmonizacao_sugerida'])}")
        else:
            st.warning("⚠️ Prato não encontrado na base. Usando análise por descrição.")
            
            # Mostra análise da descrição
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if analise_prato["categorias"]:
                    st.success("📋 **Categorias Identificadas**")
                    for cat in analise_prato["categorias"]:
                        st.write(f"- {cat['categoria'].replace('_', ' ').title()}")
            
            with col2:
                if analise_prato["metodos_preparo"]:
                    st.info("👨‍🍳 **Métodos de Preparo**")
                    for metodo in analise_prato["metodos_preparo"]:
                        st.write(f"- {metodo.title()}")
            
            with col3:
                if analise_prato["ingredientes_especificos"]:
                    st.warning("🧂 **Ingredientes Chave**")
                    for ingrediente in analise_prato["ingredientes_especificos"]:
                        st.write(f"- {ingrediente.title()}")
        
        # Recomendação inteligente
        with st.spinner('🍷 Buscando harmonizações perfeitas...'):
            recomendacoes = recomendacao_inteligente(prato_encontrado, analise_prato, dados_vinhos)
        
        st.subheader("🎯 Recomendações de Harmonização")
        
        if recomendacoes:
            st.success(f"🎉 Encontrei {len(recomendacoes)} harmonizações perfeitas!")
            
            for i, vinho in enumerate(recomendacoes, 1):
                with st.container():
                    st.markdown(f"### 🥇 {i}. {vinho['nome']}")
                    
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.write(f"**Tipo:** {vinho['tipo']}")
                        st.write(f"**Perfil:** {vinho.get('perfil', 'Equilibrado').title()}")
                        st.write(f"**Intensidade:** {vinho.get('intensidade', 'Média').title()}")
                        st.write(f"**Notas:** {', '.join(vinho.get('notas', []))}")
                    
                    with col2:
                        with st.spinner('Gerando análise detalhada...'):
                            justificativa = gerar_justificativa_avancada(prato_encontrado, analise_prato, vinho)
                            st.info(justificativa)
                    
                    st.divider()
        else:
            st.warning("🤔 Não encontrei harmonizações específicas. Aqui estão algumas sugestões gerais:")
            col1, col2 = st.columns(2)
            for i, vinho in enumerate(dados_vinhos[:4]):
                with col1 if i % 2 == 0 else col2:
                    with st.container():
                        st.write(f"**{vinho['nome']}** - {vinho['tipo']}")
                        st.write(f"*{', '.join(vinho.get('notas', ['Notas suaves'])[:2])}...*")
    else:
        st.error("Por favor, selecione ou descreva um prato.")

# Seções informativas
with st.expander("📁 Base de Dados de Pratos"):
    if dados_pratos:
        st.write(f"Total de pratos: {len(dados_pratos)}")
        
        df_data = []
        for prato in dados_pratos:
            df_data.append({
                'Nome': prato.get('nome', 'N/A'),
                'Categoria': prato.get('categoria', 'N/A').replace('_', ' ').title(),
                'Intensidade': prato.get('intensidade', 'N/A').title(),
                'Ingredientes': ', '.join(prato.get('ingredientes', []))[:50] + '...'
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df)
    else:
        st.write("Nenhum prato carregado")

with st.expander("📁 Base de Dados de Vinhos"):
    if dados_vinhos:
        st.write(f"Total de vinhos: {len(dados_vinhos)}")
        
        df_data = []
        for vinho in dados_vinhos:
            df_data.append({
                'Nome': vinho.get('nome', 'N/A'),
                'Tipo': vinho.get('tipo', 'N/A'),
                'Perfil': vinho.get('perfil', 'N/A').title(),
                'Intensidade': vinho.get('intensidade', 'N/A').title()
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df)
    else:
        st.write("Nenhum vinho carregado")