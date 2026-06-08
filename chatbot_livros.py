
import re
import sys
import random
import difflib
import threading
import unicodedata
import subprocess

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    import speech_recognition as sr
    VOZ_ENTRADA_OK = True
except Exception:
    VOZ_ENTRADA_OK = False

try:
    import pyttsx3
    VOZ_SAIDA_OK = True
except Exception:
    VOZ_SAIDA_OK = False


def load_nlp():

    desativar = ["parser", "ner"]
    try:
        return spacy.load("pt_core_news_sm", disable=desativar)
    except Exception:
        try:
            subprocess.check_call(
                [sys.executable, "-m", "spacy", "download", "pt_core_news_sm"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return spacy.load("pt_core_news_sm", disable=desativar)
        except Exception:
            nlp = spacy.blank("pt")
            if "sentencizer" not in nlp.pipe_names:
                nlp.add_pipe("sentencizer")
            return nlp


def remove_acentos(texto: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFD", texto)
        if unicodedata.category(ch) != "Mn"
    )


TONS_CONFORTO = {
    "leve", "divertido", "acolhedor", "reconfortante", "inspirador",
    "engracado", "motivacional", "calmo", "esperancoso"
}

VIBES = {
    "tristeza": {
        "tons": {"leve", "reconfortante", "inspirador", "acolhedor", "esperancoso", "divertido", "calmo"},
        "curto": True,
        "motivo": "tem um clima leve/reconfortante para levantar o astral",
        "intros": [
            "Sinto muito que o dia tenha sido difícil. 💛 Separei leituras mais leves pra confortar:",
            "Poxa, dia pesado... 💛 Que tal uma história mais leve pra dar uma respirada?",
            "Tô aqui com você. Olha essas opções acolhedoras pra animar um pouco:",
        ],
    },
    "ansiedade": {
        "tons": {"leve", "calmo", "reconfortante", "acolhedor", "esperancoso", "inspirador"},
        "curto": True,
        "motivo": "tem um tom calmo e acolhedor pra ajudar a desacelerar",
        "intros": [
            "Respira fundo. 💛 Que tal algo mais calmo e leve pra ajudar a relaxar?",
            "Ansiedade é osso... separei leituras tranquilas pra desacelerar a cabeça:",
            "Vamos com calma. Olha essas opções mais leves e acolhedoras:",
        ],
    },
    "raiva": {
        "tons": {"divertido", "leve", "envolvente", "epico", "catartico"},
        "curto": False,
        "motivo": "ajuda a desanuviar e extravasar",
        "intros": [
            "Parece que bateu uma raiva... 😮‍💨 Que tal um livro pra desanuviar?",
            "Dia de nervos? Separei histórias envolventes pra descarregar a cabeça:",
            "Bora canalizar essa energia numa boa leitura:",
        ],
    },
    "tedio": {
        "tons": {"envolvente", "rapido", "tenso", "aventureiro", "epico", "divertido"},
        "curto": False,
        "motivo": "é um prende-do-início-ao-fim pra matar o tédio",
        "intros": [
            "Entediado? 😏 Separei umas histórias que prendem do início ao fim:",
            "Bora espantar o tédio com uns livros bem envolventes:",
            "Que tal algo viciante pra não largar? Olha essas:",
        ],
    },
    "cansaco": {
        "tons": {"leve", "reconfortante", "divertido", "acolhedor", "calmo"},
        "curto": True,
        "motivo": "é leve e gostoso de ler sem cansar",
        "intros": [
            "Dia cansativo, né? Separei leituras leves que não pesam:",
            "Pra descansar a mente, que tal algo leve e gostoso de ler?",
            "Nada de livro denso agora. Olha essas opções levinhas:",
        ],
    },
    "medo": {
        "tons": {"leve", "reconfortante", "acolhedor", "divertido", "calmo"},
        "curto": True,
        "motivo": "traz um clima acolhedor e tranquilo",
        "intros": [
            "Ei, tá tudo bem. 💛 Que tal uma leitura mais acolhedora e tranquila?",
            "Pra acalmar, separei umas histórias leves e reconfortantes:",
        ],
    },
    "empolgacao": {
        "tons": {"epico", "aventureiro", "envolvente", "divertido"},
        "curto": False,
        "motivo": "tem a mesma energia que você tá sentindo",
        "intros": [
            "Que energia boa! 😄 Bora canalizar nessas aventuras:",
            "Adorei o ânimo! Separei histórias à altura do seu pique:",
            "Com esse astral, essas aqui vão te empolgar:",
        ],
    },
}

class AnalisadorSentimento:

    def __init__(self):
        self.positivas = {
            "amor", "amo", "amei", "adoro", "adorei", "amar", "adorar", "gosto",
            "gostei", "gostar", "curti", "otimo", "otima", "excelente",
            "maravilhoso", "maravilhosa", "maravilha", "incrivel", "fantastico",
            "fantastica", "sensacional", "espetacular", "perfeito", "perfeita",
            "bom", "boa", "legal", "bacana", "massa", "show", "top", "feliz",
            "felicidade", "alegre", "alegria", "animado", "animada", "empolgado",
            "empolgada", "contente", "satisfeito", "satisfeita", "lindo", "linda",
            "belo", "bela", "divertido", "divertida", "tranquilo", "tranquila",
            "calmo", "paz", "esperanca", "grato", "grata", "gratidao", "sucesso",
            "vitoria", "melhor", "melhorou", "amado", "querido", "fofo", "fofa",
            "encantado", "encantada", "apaixonado", "apaixonada", "empolgante",
            "emocionante", "inspirador", "motivado", "motivada", "aliviado",
            "aliviada", "sorrindo", "rindo", "otimismo", "esperancoso",
            "irado", "daora", "maneiro", "arraso", "radiante", "euforico",
            "euforica", "realizado", "realizada", "orgulhoso", "orgulhosa"
        }
        self.negativas = {
            "odeio", "odiei", "odiar", "detesto", "detestei", "detestar", "ruim",
            "pessimo", "pessima", "horrivel", "horroroso", "horrorosa", "terrivel",
            "triste", "tristeza", "deprimido", "deprimida", "depre", "chateado",
            "chateada", "irritado", "irritada", "raiva", "bravo", "brava",
            "furioso", "furiosa", "cansado", "cansada", "exausto", "exausta",
            "estressado", "estressada", "frustrado", "frustrada", "decepcionado",
            "decepcionada", "decepcao", "medo", "assustado", "ansioso", "ansiosa",
            "ansiedade", "sozinho", "sozinha", "solidao", "chato", "chata",
            "tedio", "entediado", "entediada", "lixo", "pior", "piorou",
            "fracasso", "derrota", "dor", "doi", "doendo", "sofrendo", "sofro",
            "sofrer", "chorar", "chorando", "chorei", "lagrimas", "perdido",
            "perdida", "vazio", "vazia", "desanimado", "desanimada", "infeliz",
            "miseravel", "angustia", "angustiado", "angustiada", "preocupado",
            "preocupada", "nervoso", "nervosa", "mal", "desastre", "problema",
            "problemas", "desespero", "desesperado", "desesperada", "magoado",
            "magoada", "arrependido", "arrependida", "abatido", "abatida",
            "derrotado", "desmotivado", "desmotivada",
            "droga", "porcaria", "merda", "bosta", "porre", "zoado", "zoada",
            "ferrado", "ferrada", "lascado", "lascada", "osso", "barra", "sufoco",
            "desgraca", "desgracado", "pavoroso", "deprimente", "frustrante",
            "decepcionante", "chateacao", "estresse", "cansativo", "cansativa",
            "exaustao", "esgotado", "esgotada", "horrendo", "horrenda",
            "apavorado", "apavorada", "revoltado", "revoltada", "puto",
            "puta", "odio", "saudade", "melancolia", "melancolico", "acabado",
            "acabada"
        }
        self.intensificadores = {
            "muito": 1.6, "super": 1.8, "extremamente": 2.0, "bastante": 1.4,
            "demais": 1.6, "tao": 1.4, "mega": 1.8, "ultra": 1.9,
            "completamente": 1.7, "totalmente": 1.7, "realmente": 1.4, "absurdamente": 1.9
        }
        self.negadores = {"nao", "nunca", "jamais", "nem", "sem", "tampouco"}

        self.frases_positivas = ["de boa", "tudo certo", "feliz da vida", "valeu a pena",
                                 "tudo otimo", "deu tudo certo", "que dia bom"]
        self.frases_negativas = ["pra baixo", "baixo astral", "saco cheio", "sem animo",
                                 "sem vontade", "de mal", "mal humorado", "nao aguento mais",
                                 "uma droga", "que droga", "foi uma droga", "que saco",
                                 "que merda", "que porcaria", "deu tudo errado",
                                 "tudo dando errado", "dia ruim", "dia horrivel",
                                 "to mal", "to pessimo", "nada da certo"]

        # 
        self.emocoes = {
            "tristeza": {"triste", "tristeza", "deprimido", "deprimida", "depre", "sozinho",
                         "sozinha", "solidao", "vazio", "vazia", "chorar", "chorando", "chorei",
                         "saudade", "melancolia", "melancolico", "desanimado", "desanimada",
                         "infeliz", "abatido", "abatida", "pra baixo", "baixo astral", "sem animo"},
            "ansiedade": {"ansioso", "ansiosa", "ansiedade", "nervoso", "nervosa", "preocupado",
                          "preocupada", "aflito", "aflita", "angustia", "angustiado", "angustiada",
                          "inseguro", "insegura", "sufoco"},
            "raiva": {"raiva", "bravo", "brava", "irritado", "irritada", "furioso", "furiosa",
                      "puto", "puta", "odio", "odeio", "revoltado", "revoltada", "estressado",
                      "estressada", "de saco cheio", "que saco", "puto da vida"},
            "medo": {"medo", "assustado", "assustada", "apavorado", "apavorada", "com medo",
                     "aterrorizado", "aterrorizada", "panico"},
            "cansaco": {"cansado", "cansada", "exausto", "exausta", "esgotado", "esgotada",
                        "sem energia", "sem forcas", "sono", "sonolento", "acabado", "acabada",
                        "cansativo"},
            "tedio": {"entediado", "entediada", "tedio", "tediante", "sem graca", "monotono",
                      "monotona", "nada pra fazer", "entediante", "que tedio"},
            "empolgacao": {"animado", "animada", "empolgado", "empolgada", "euforico", "euforica",
                           "radiante", "motivado", "motivada", "feliz da vida", "muito feliz",
                           "realizado", "realizada"},
        }
        # Ordem de prioridade para desempate na detecção de emoção.
        self._ordem_emocao = ["tristeza", "ansiedade", "raiva", "medo", "cansaco", "tedio", "empolgacao"]

        self.emojis_positivos = set("😀😃😄😁😊🙂😍🥰😘😎🥳😂🤣😆👍❤🎉✨🥹😌")
        self.emojis_negativos = set("😢😭😞😔😟😡🤬👎💔😩😫😖😣🙁☹😤😪😠😰😨")

    def analisar(self, texto: str) -> dict:  
        bruto = texto or ""

        # 1) Emojis
        score = 0.0
        for ch in bruto:
            if ch in self.emojis_positivos:
                score += 0.9
            elif ch in self.emojis_negativos:
                score -= 0.9

        # 2) Expressões de duas palavras
        t = remove_acentos(bruto.lower())
        for frase in self.frases_positivas:
            if frase in t:
                score += 1.2
        for frase in self.frases_negativas:
            if frase in t:
                score -= 1.4

        clausulas = re.split(r"[,.;:!?]|\bmas\b|\bporem\b|\bcontudo\b|\bentretanto\b|\btodavia\b", t)

        for clausula in clausulas:
            tokens = re.findall(r"[a-z]+", clausula)
            negacao = False
            intensidade = 1.0

            for tok in tokens:
                if tok in self.negadores:
                    negacao = True
                    continue
                if tok in self.intensificadores:
                    intensidade = self.intensificadores[tok]
                    continue

                valor = 0.0
                if tok in self.positivas:
                    valor = 1.0
                elif tok in self.negativas:
                    valor = -1.0

                if valor != 0.0:
                    valor *= intensidade
                    if negacao:
                        valor *= -1.0      
                        negacao = False    
                    score += valor
                    intensidade = 1.0

        # 4) Normaliza para [-1, 1] e classifica
        compound = max(-1.0, min(1.0, score / 4.0))
        if compound >= 0.25:
            label, emoji = "positivo", "😊"
        elif compound <= -0.25:
            label, emoji = "negativo", "😟"
        else:
            label, emoji = "neutro", "😐"

        emocao = self.detectar_emocao(t)

        return {"label": label, "emoji": emoji, "compound": round(compound, 3),
                "score": round(score, 2), "emocao": emocao}

    def detectar_emocao(self, texto_sem_acento: str):
        """Detecta a emoção predominante (ou None). 'texto_sem_acento' já vem normalizado."""
        contagem = {}
        for emo, termos in self.emocoes.items():
            c = 0
            for termo in termos:
                if " " in termo:
                    if termo in texto_sem_acento:
                        c += 1
                elif re.search(r"\b" + re.escape(termo) + r"\b", texto_sem_acento):
                    c += 1
            if c:
                contagem[emo] = c

        if not contagem:
            return None
        melhor, maxc = None, 0
        for emo in self._ordem_emocao:
            if contagem.get(emo, 0) > maxc:
                maxc = contagem[emo]
                melhor = emo
        return melhor


class ChatbotLivros:
    def __init__(self):
        self.nlp = load_nlp()
        self.analisador = AnalisadorSentimento()
        self.ultimo_sentimento = {"label": "neutro", "emoji": "😐", "compound": 0.0, "score": 0.0, "emocao": None}

        # --- Bancos de respostas randômicas (parte "randômica" do chat híbrido) ---
        self.saudações_entrada = {
            "oi", "ola", "olá", "bom dia", "boa tarde", "boa noite", "eai", "e aí", "hey"
        }
        self.saudações_saida = [
            "Oi! Eu sou o BookBot, especialista em recomendação de livros. Me diga do que você gosta :).",
            "Olá! Posso sugerir livros por gênero, tema, hobby ou clima de leitura. Por onde começamos?",
            "Seja bem-vindo(a)! Fale algo como: 'gosto de fantasia, magia e aventura'.",
            "E aí! Bora achar seu próximo livro? Me conta um gênero, um tema ou um livro que você curtiu."
        ]
        self.despedidas = {"tchau", "adeus", "valeu", "obrigado", "obrigada", "falou", "ate logo", "até logo"}
        self.despedidas_saida = [
            "Foi um prazer! Quando quiser novas recomendações, é só chamar. 📚",
            "Até a próxima! Boa leitura. 😊",
            "Falou! Volte sempre que quiser uma indicação.",
            "Por nada! Espero ter ajudado. Boas páginas pela frente. 📖"
        ]
        self.acks_positivos = [
            "Que energia boa! 😄",
            "Adorei o ânimo!",
            "Show de bola!",
            "Que astral ótimo!"
        ]
        self.respostas_neutras_sem_sinal = [
            "Me conta um pouco mais: um gênero, um tema ou um livro que você gostou.",
            "Posso recomendar por gênero (fantasia, romance, suspense...), tema ou clima. O que te atrai hoje?",
            "Diga algo como 'quero suspense com investigação' ou 'fale sobre Duna' que eu te ajudo."
        ]
        # Introduções randômicas para a recomendação, de acordo com o humor.
        self.intros_conforto = [
            "Sinto muito que o dia esteja difícil. 💛 Separei leituras mais leves que costumam confortar:",
            "Poxa, parece pesado agora. Que tal algo mais leve pra dar uma respirada?",
            "Tô aqui com você. 💛 Olha essas opções mais acolhedoras pra animar:",
            "Às vezes uma boa história ajuda a aliviar. Veja estas sugestões reconfortantes:"
        ]
        self.intros_positivos = [
            "Bora aproveitar o pique com estas indicações:",
            "Acho que você vai curtir muito estas:",
            "Com esse ânimo, separei estas recomendações:"
        ]
        self.intros_neutros = [
            "Encontrei estas recomendações para você:",
            "Com base no que você disse, acho que estas combinam:",
            "Olha o que separei pra você:"
        ]

        self.generos_keywords = {
            "fantasia": {"fantasia", "magia", "mago", "feiticeiro", "dragao", "dragão", "reino", "espada", "mitologia"},
            "ficção científica": {"ficcao cientifica", "ficção científica", "sci-fi", "scifi", "tecnologia", "espaco", "espaço", "robo", "robô", "futuro", "planeta", "nave"},
            "mistério/suspense": {"misterio", "mistério", "suspense", "crime", "detetive", "investigacao", "investigação", "assassinato", "serial killer", "thriller"},
            "romance": {"romance", "amor", "casal", "relacionamento", "emocionante", "fofo", "apaixonante"},
            "distopia": {"distopia", "regime", "controle", "opressao", "opressão", "sobrevivencia", "sobrevivência", "futuro sombrio", "sociedade"},
            "aventura": {"aventura", "jornada", "viagem", "exploracao", "exploração", "tesouro", "missao", "missão", "epico", "épico"},
            "clássico": {"classico", "clássico", "literatura", "canonico", "canônico"},
            "terror": {"terror", "horror", "assombrado", "fantasma", "vampiro", "sobrenatural", "macabro", "susto"},
            "não-ficção": {"nao ficcao", "não ficção", "autoajuda", "autoconhecimento", "habito", "hábito", "produtividade", "historia real", "biografia", "ciencia real"},
            "nacional": {"nacional", "brasileiro", "brasileira", "literatura brasileira", "machado", "clarice", "jorge amado"},
            "drama": {"drama", "dramatico", "comovente", "emotivo", "superacao", "superação", "drama familiar"},
            "infantojuvenil": {"infantil", "juvenil", "infantojuvenil", "crianca", "criança", "leitura jovem"}
        }

        self.keywords_extras = {
            "curto": {"curto", "rapido", "rápido", "leve", "simples"},
            "longo": {"longo", "grande", "denso", "complexo"},
            "reflexivo": {"filosofia", "reflexivo", "profundo", "politica", "política", "social"},
            "divertido": {"humor", "engraçado", "engracado", "divertido", "leve"},
            "sombrio": {"sombrio", "pesado", "tenso", "dark"},
            "inspirador": {"inspirador", "motivacional", "motivacao", "motivação", "superacao", "superação", "esperanca", "esperança"}
        }

        self.faq = [
            {
                "pergunta": "quais generos voce recomenda",
                "resposta": "Eu trabalho com fantasia, ficção científica, mistério/suspense, romance, distopia, aventura, terror, não-ficção, clássicos e literatura nacional."
            },
            {
                "pergunta": "como voce funciona",
                "resposta": "Sou um chatbot híbrido: uso regras e respostas variadas (randômicas) para conversar e TF-IDF com similaridade de cosseno para comparar seu pedido com a base de livros. Também analiso o seu humor para adaptar o tom e as sugestões."
            },
            {
                "pergunta": "me de exemplos de perguntas",
                "resposta": "Você pode escrever: 'quero algo com magia e amizade', 'gosto de suspense policial', 'procuro romance leve' ou 'quero ficção científica com política'."
            },
            {
                "pergunta": "qual a diferenca entre fantasia e ficcao cientifica",
                "resposta": "Fantasia trabalha com magia, criaturas e mundos fantásticos. Ficção científica explora tecnologia, ciência, futuro, espaço e seus impactos sociais."
            },
            {
                "pergunta": "quero comecar a ler",
                "resposta": "Para começar, eu sugiro livros acessíveis e envolventes, como O Hobbit, Percy Jackson, O Pequeno Príncipe ou Jogos Vorazes."
            },
            {
                "pergunta": "voce entende voz",
                "resposta": "Entendo! Clique no botão '🎤 Falar' e diga sua preferência. Eu também posso ler as respostas em voz alta se você marcar '🔊 Falar respostas'."
            }
        ]

        self.livros = [
            {
                "titulo": "O Hobbit", "autor": "J. R. R. Tolkien", "genero": "fantasia",
                "elementos": ["aventura", "jornada", "dragao", "amizade", "mundo fantastico"],
                "hobbies": ["rpg", "games", "mitologia", "mapas", "aventura"],
                "tom": ["leve", "epico", "acolhedor"], "tamanho": "médio",
                "descricao": "Bilbo Bolseiro sai do conforto de sua casa para uma grande aventura com anões, um mago e um dragão."
            },
            {
                "titulo": "Harry Potter e a Pedra Filosofal", "autor": "J. K. Rowling", "genero": "fantasia",
                "elementos": ["magia", "amizade", "escola", "misterio", "aventura"],
                "hobbies": ["filmes", "series", "fantasia", "jogos"],
                "tom": ["leve", "envolvente", "acolhedor"], "tamanho": "médio",
                "descricao": "Um garoto descobre que é bruxo e entra em uma escola de magia, onde enfrenta mistérios e faz grandes amizades."
            },
            {
                "titulo": "Percy Jackson e o Ladrão de Raios", "autor": "Rick Riordan", "genero": "fantasia",
                "elementos": ["mitologia", "aventura", "humor", "amizade", "missao"],
                "hobbies": ["mitologia", "games", "aventura", "humor"],
                "tom": ["leve", "divertido"], "tamanho": "médio",
                "descricao": "Percy descobre ser filho de um deus grego e embarca em uma missão cheia de monstros, deuses e humor."
            },
            {
                "titulo": "O Nome do Vento", "autor": "Patrick Rothfuss", "genero": "fantasia",
                "elementos": ["magia", "musica", "aventura", "universidade", "lenda"],
                "hobbies": ["fantasia", "musica", "worldbuilding"],
                "tom": ["poetico", "imersivo", "complexo"], "tamanho": "longo",
                "descricao": "Kvothe narra sua trajetória de músico talentoso a figura lendária em um universo rico e detalhado."
            },
            {
                "titulo": "As Crônicas de Nárnia: O Leão, a Feiticeira e o Guarda-Roupa", "autor": "C. S. Lewis", "genero": "fantasia",
                "elementos": ["magia", "mundo fantastico", "aventura", "amizade", "bem contra mal"],
                "hobbies": ["fantasia", "filmes", "familia"],
                "tom": ["leve", "acolhedor", "magico"], "tamanho": "curto",
                "descricao": "Quatro irmãos atravessam um guarda-roupa e chegam a Nárnia, um reino mágico em guerra contra uma feiticeira."
            },
            {
                "titulo": "O Senhor dos Anéis: A Sociedade do Anel", "autor": "J. R. R. Tolkien", "genero": "fantasia",
                "elementos": ["aventura", "jornada", "amizade", "guerra", "mundo fantastico"],
                "hobbies": ["rpg", "mitologia", "mapas", "games"],
                "tom": ["epico", "imersivo", "complexo"], "tamanho": "longo",
                "descricao": "Frodo recebe a missão de destruir um anel poderoso e parte em uma jornada épica com a Sociedade do Anel."
            },
            {
                "titulo": "Duna", "autor": "Frank Herbert", "genero": "ficção científica",
                "elementos": ["politica", "ecologia", "religiao", "profecia", "deserto"],
                "hobbies": ["ciencia", "xadrez", "debates", "historia"],
                "tom": ["epico", "reflexivo", "complexo"], "tamanho": "longo",
                "descricao": "Em Arrakis, um planeta desértico vital para o império, Paul Atreides se envolve em política, profecia e sobrevivência."
            },
            {
                "titulo": "Fundação", "autor": "Isaac Asimov", "genero": "ficção científica",
                "elementos": ["futuro", "ciencia", "politica", "imperio", "estrategia"],
                "hobbies": ["ciencia", "historia", "tecnologia", "xadrez"],
                "tom": ["inteligente", "reflexivo"], "tamanho": "médio",
                "descricao": "Hari Seldon tenta reduzir o caos de milênios com a psico-história em uma saga sobre ciência, poder e civilização."
            },
            {
                "titulo": "Neuromancer", "autor": "William Gibson", "genero": "ficção científica",
                "elementos": ["tecnologia", "hacker", "inteligencia artificial", "cyberpunk", "crime"],
                "hobbies": ["programacao", "games", "tecnologia", "ciberseguranca"],
                "tom": ["sombrio", "rapido", "urbano"], "tamanho": "médio",
                "descricao": "Um hacker decadente é recrutado para uma missão de alto risco em um futuro dominado por redes, megacorporações e IA."
            },
            {
                "titulo": "O Guia do Mochileiro das Galáxias", "autor": "Douglas Adams", "genero": "ficção científica",
                "elementos": ["espaco", "humor", "viagem", "absurdo", "aventura"],
                "hobbies": ["humor", "cultura pop", "series", "aventura"],
                "tom": ["divertido", "leve", "engracado"], "tamanho": "curto",
                "descricao": "Arthur Dent descobre que a Terra será destruída e acaba envolvido em uma aventura espacial completamente absurda."
            },
            {
                "titulo": "1984", "autor": "George Orwell", "genero": "distopia",
                "elementos": ["controle", "vigilancia", "politica", "sociedade", "opressao"],
                "hobbies": ["politica", "filosofia", "sociologia", "debates"],
                "tom": ["sombrio", "reflexivo"], "tamanho": "médio",
                "descricao": "Winston Smith vive sob vigilância constante em uma sociedade totalitária em que até o pensamento é controlado."
            },
            {
                "titulo": "Jogos Vorazes", "autor": "Suzanne Collins", "genero": "distopia",
                "elementos": ["sobrevivencia", "acao", "competicao", "critica social", "aventura"],
                "hobbies": ["games", "acao", "series", "aventura"],
                "tom": ["envolvente", "rapido"], "tamanho": "médio",
                "descricao": "Katniss precisa lutar por sobrevivência em um reality mortal que revela a desigualdade e a crueldade do sistema."
            },
            {
                "titulo": "Admirável Mundo Novo", "autor": "Aldous Huxley", "genero": "distopia",
                "elementos": ["sociedade", "tecnologia", "controle", "consumo", "ciencia"],
                "hobbies": ["filosofia", "sociologia", "ciencia", "debates"],
                "tom": ["reflexivo", "frio"], "tamanho": "médio",
                "descricao": "Uma sociedade aparentemente perfeita se sustenta por condicionamento, consumo e controle biotecnológico."
            },
            {
                "titulo": "Assassinato no Expresso do Oriente", "autor": "Agatha Christie", "genero": "mistério/suspense",
                "elementos": ["detetive", "investigacao", "crime", "pistas", "quebra-cabeca"],
                "hobbies": ["enigmas", "podcasts true crime", "jogos de misterio"],
                "tom": ["inteligente", "envolvente"], "tamanho": "curto",
                "descricao": "Hercule Poirot investiga um assassinato em um trem de luxo, reunindo pistas e suspeitos em um caso clássico."
            },
            {
                "titulo": "Um Estudo em Vermelho", "autor": "Arthur Conan Doyle", "genero": "mistério/suspense",
                "elementos": ["detetive", "investigacao", "logica", "crime", "deducao"],
                "hobbies": ["xadrez", "enigmas", "investigacao", "series"],
                "tom": ["classico", "inteligente"], "tamanho": "curto",
                "descricao": "Primeira aventura de Sherlock Holmes, em que lógica e observação conduzem à solução de um assassinato."
            },
            {
                "titulo": "A Garota no Trem", "autor": "Paula Hawkins", "genero": "mistério/suspense",
                "elementos": ["suspense", "segredos", "narrador duvidoso", "crime"],
                "hobbies": ["series", "thrillers", "psicologia"],
                "tom": ["sombrio", "tenso"], "tamanho": "médio",
                "descricao": "Uma mulher se envolve em um desaparecimento ao observar, da janela do trem, a rotina de pessoas desconhecidas."
            },
            {
                "titulo": "O Código Da Vinci", "autor": "Dan Brown", "genero": "mistério/suspense",
                "elementos": ["enigma", "investigacao", "historia", "arte", "perseguicao"],
                "hobbies": ["enigmas", "historia", "arte", "viagens"],
                "tom": ["rapido", "envolvente"], "tamanho": "médio",
                "descricao": "Um simbologista decifra códigos escondidos em obras de arte enquanto foge e investiga um segredo milenar."
            },
            {
                "titulo": "Orgulho e Preconceito", "autor": "Jane Austen", "genero": "romance",
                "elementos": ["amor", "dialogos", "sociedade", "humor", "classico"],
                "hobbies": ["filmes", "dramas", "historia", "relacoes humanas"],
                "tom": ["leve", "ironico", "elegante"], "tamanho": "médio",
                "descricao": "Elizabeth Bennet e Mr. Darcy atravessam mal-entendidos, orgulho e crítica social em um romance clássico."
            },
            {
                "titulo": "Como Eu Era Antes de Você", "autor": "Jojo Moyes", "genero": "romance",
                "elementos": ["amor", "emocao", "transformacao", "drama"],
                "hobbies": ["dramas", "filmes", "historias emocionantes"],
                "tom": ["emocionante", "sensivel"], "tamanho": "médio",
                "descricao": "Louisa e Will constroem uma relação transformadora, marcada por afeto, humor e decisões difíceis."
            },
            {
                "titulo": "A Hipótese do Amor", "autor": "Ali Hazelwood", "genero": "romance",
                "elementos": ["amor", "universidade", "ciencia", "humor", "fake dating"],
                "hobbies": ["ciencia", "series", "romcom", "universidade"],
                "tom": ["leve", "divertido", "emocionante"], "tamanho": "médio",
                "descricao": "Uma aluna de doutorado entra em um relacionamento falso que rapidamente complica sua vida acadêmica e afetiva."
            },
            {
                "titulo": "A Culpa é das Estrelas", "autor": "John Green", "genero": "romance",
                "elementos": ["amor", "doenca", "juventude", "emocao", "drama"],
                "hobbies": ["dramas", "filmes", "poesia"],
                "tom": ["emocionante", "sensivel"], "tamanho": "médio",
                "descricao": "Dois jovens que se conhecem em um grupo de apoio vivem um romance intenso diante da fragilidade da vida."
            },
            {
                "titulo": "O Diário de Bridget Jones", "autor": "Helen Fielding", "genero": "romance",
                "elementos": ["amor", "humor", "cotidiano", "autoironia"],
                "hobbies": ["comedia romantica", "filmes", "series"],
                "tom": ["divertido", "leve", "engracado"], "tamanho": "médio",
                "descricao": "Bridget narra com humor seus perrengues amorosos e profissionais em um diário cheio de autoironia."
            },
            {
                "titulo": "A Coisa", "autor": "Stephen King", "genero": "terror",
                "elementos": ["palhaco", "medo", "infancia", "amizade", "sobrenatural"],
                "hobbies": ["terror", "series", "filmes"],
                "tom": ["sombrio", "tenso", "assustador"], "tamanho": "longo",
                "descricao": "Um grupo de amigos enfrenta, na infância e na vida adulta, uma entidade que se alimenta do medo na cidade de Derry."
            },
            {
                "titulo": "Drácula", "autor": "Bram Stoker", "genero": "terror",
                "elementos": ["vampiro", "sobrenatural", "gotico", "medo", "classico"],
                "hobbies": ["terror", "historia", "literatura gotica"],
                "tom": ["sombrio", "gotico"], "tamanho": "médio",
                "descricao": "Cartas e diários narram a chegada do Conde Drácula à Inglaterra e a luta para detê-lo neste clássico do terror."
            },
            {
                "titulo": "O Iluminado", "autor": "Stephen King", "genero": "terror",
                "elementos": ["hotel", "isolamento", "loucura", "sobrenatural", "medo"],
                "hobbies": ["terror", "psicologia", "filmes"],
                "tom": ["sombrio", "tenso", "assustador"], "tamanho": "médio",
                "descricao": "Uma família isolada em um hotel durante o inverno enfrenta forças sobrenaturais e a sanidade em colapso."
            },
            {
                "titulo": "Cem Anos de Solidão", "autor": "Gabriel García Márquez", "genero": "clássico",
                "elementos": ["familia", "realismo magico", "tempo", "destino", "saga"],
                "hobbies": ["literatura", "historia", "filosofia"],
                "tom": ["poetico", "reflexivo", "imersivo"], "tamanho": "longo",
                "descricao": "A saga da família Buendía em Macondo mistura realismo e magia ao longo de gerações marcadas pela solidão."
            },
            {
                "titulo": "Dom Casmurro", "autor": "Machado de Assis", "genero": "nacional",
                "elementos": ["ciume", "amor", "duvida", "narrador duvidoso", "classico"],
                "hobbies": ["literatura brasileira", "debates", "historia"],
                "tom": ["ironico", "reflexivo", "classico"], "tamanho": "médio",
                "descricao": "Bento Santiago narra sua história com Capitu e a dúvida sobre uma traição que nunca se confirma de fato."
            },
            {
                "titulo": "Capitães da Areia", "autor": "Jorge Amado", "genero": "nacional",
                "elementos": ["infancia", "rua", "amizade", "critica social", "bahia"],
                "hobbies": ["literatura brasileira", "historia", "sociologia"],
                "tom": ["emocionante", "reflexivo"], "tamanho": "médio",
                "descricao": "Um grupo de meninos de rua de Salvador sobrevive entre afetos, aventuras e a dureza da desigualdade."
            },
            {
                "titulo": "A Hora da Estrela", "autor": "Clarice Lispector", "genero": "nacional",
                "elementos": ["solidao", "existencia", "nordeste", "introspeccao"],
                "hobbies": ["literatura brasileira", "filosofia", "poesia"],
                "tom": ["reflexivo", "sensivel", "poetico"], "tamanho": "curto",
                "descricao": "A breve e tocante história de Macabéa, uma jovem nordestina anônima, narrada com profundidade existencial."
            },
            {
                "titulo": "O Pequeno Príncipe", "autor": "Antoine de Saint-Exupéry", "genero": "clássico",
                "elementos": ["amizade", "infancia", "sentido da vida", "fabula", "amor"],
                "hobbies": ["reflexao", "familia", "poesia"],
                "tom": ["leve", "reconfortante", "inspirador"], "tamanho": "curto",
                "descricao": "Um piloto encontra no deserto um pequeno príncipe cujas histórias revelam lições sobre amor, amizade e o essencial da vida."
            },
            {
                "titulo": "O Alquimista", "autor": "Paulo Coelho", "genero": "ficção científica",
                "elementos": ["jornada", "sonho", "destino", "autoconhecimento", "viagem"],
                "hobbies": ["reflexao", "viagens", "filosofia"],
                "tom": ["inspirador", "leve", "reflexivo"], "tamanho": "curto",
                "descricao": "O pastor Santiago parte em busca de um tesouro e descobre, na jornada, lições sobre seguir a própria lenda pessoal."
            },
            {
                "titulo": "O Conde de Monte Cristo", "autor": "Alexandre Dumas", "genero": "aventura",
                "elementos": ["vinganca", "prisao", "fortuna", "justica", "intriga"],
                "hobbies": ["aventura", "historia", "estrategia"],
                "tom": ["epico", "envolvente"], "tamanho": "longo",
                "descricao": "Traído e preso injustamente, Edmond Dantès foge, enriquece e arquiteta uma elaborada vingança contra seus algozes."
            },
            {
                "titulo": "A Volta ao Mundo em 80 Dias", "autor": "Júlio Verne", "genero": "aventura",
                "elementos": ["viagem", "aposta", "exploracao", "corrida", "mundo"],
                "hobbies": ["viagens", "aventura", "geografia"],
                "tom": ["leve", "divertido", "aventureiro"], "tamanho": "médio",
                "descricao": "Phileas Fogg aposta que dará a volta ao mundo em 80 dias e enfrenta imprevistos por vários continentes."
            },
            {
                "titulo": "O Diário de Anne Frank", "autor": "Anne Frank", "genero": "não-ficção",
                "elementos": ["guerra", "esconderijo", "esperanca", "historia real", "juventude"],
                "hobbies": ["historia", "biografia", "reflexao"],
                "tom": ["emocionante", "sensivel", "inspirador"], "tamanho": "médio",
                "descricao": "O diário real de uma adolescente judia escondida durante a Segunda Guerra, entre o medo e a esperança."
            },
            {
                "titulo": "Sapiens: Uma Breve História da Humanidade", "autor": "Yuval Noah Harari", "genero": "não-ficção",
                "elementos": ["historia", "evolucao", "sociedade", "ciencia", "cultura"],
                "hobbies": ["historia", "ciencia", "debates", "filosofia"],
                "tom": ["inteligente", "reflexivo"], "tamanho": "longo",
                "descricao": "Uma viagem pela história da espécie humana, das primeiras tribos às revoluções que moldaram o mundo atual."
            },
            {
                "titulo": "O Poder do Hábito", "autor": "Charles Duhigg", "genero": "não-ficção",
                "elementos": ["habitos", "comportamento", "produtividade", "ciencia", "mudanca"],
                "hobbies": ["produtividade", "autoconhecimento", "ciencia"],
                "tom": ["inspirador", "motivacional", "leve"], "tamanho": "médio",
                "descricao": "Como os hábitos se formam e como entendê-los pode transformar a vida pessoal, as empresas e a sociedade."
            },
            {
                "titulo": "Mindset: A Nova Psicologia do Sucesso", "autor": "Carol S. Dweck", "genero": "não-ficção",
                "elementos": ["mentalidade", "aprendizado", "superacao", "psicologia"],
                "hobbies": ["autoconhecimento", "produtividade", "psicologia"],
                "tom": ["inspirador", "motivacional"], "tamanho": "médio",
                "descricao": "A diferença entre a mentalidade fixa e a de crescimento e como ela influencia o sucesso e a realização pessoal."
            },
            # ----- Títulos voltados a diferentes humores (feel-good, vira-página, drama, etc.) -----
            {
                "titulo": "A Biblioteca da Meia-Noite", "autor": "Matt Haig", "genero": "drama",
                "elementos": ["segunda chance", "vidas possiveis", "arrependimento", "esperanca", "escolhas"],
                "hobbies": ["reflexao", "filosofia", "autoconhecimento"],
                "tom": ["reconfortante", "inspirador", "esperancoso", "emocionante", "calmo"], "tamanho": "médio",
                "descricao": "Entre a vida e a morte, Nora encontra uma biblioteca onde pode viver as vidas que poderia ter tido — uma história sobre esperança e recomeços."
            },
            {
                "titulo": "Extraordinário", "autor": "R. J. Palacio", "genero": "drama",
                "elementos": ["bondade", "aceitacao", "escola", "amizade", "superacao"],
                "hobbies": ["familia", "reflexao", "filmes"],
                "tom": ["acolhedor", "emocionante", "inspirador", "esperancoso"], "tamanho": "médio",
                "descricao": "August, um menino com uma diferença facial, entra na escola pela primeira vez e ensina a todos sobre empatia, coragem e gentileza."
            },
            {
                "titulo": "A Menina que Roubava Livros", "autor": "Markus Zusak", "genero": "drama",
                "elementos": ["guerra", "livros", "amizade", "perda", "esperanca"],
                "hobbies": ["historia", "leitura", "reflexao"],
                "tom": ["emocionante", "sensivel", "reflexivo"], "tamanho": "longo",
                "descricao": "Narrada pela Morte, a história de Liesel, uma menina que encontra conforto nos livros na Alemanha nazista."
            },
            {
                "titulo": "O Caçador de Pipas", "autor": "Khaled Hosseini", "genero": "drama",
                "elementos": ["amizade", "culpa", "redencao", "familia", "afeganistao"],
                "hobbies": ["reflexao", "historia", "dramas"],
                "tom": ["emocionante", "sensivel", "reflexivo"], "tamanho": "médio",
                "descricao": "Amir busca redenção por uma traição de infância em uma comovente história de amizade e perdão no Afeganistão."
            },
            {
                "titulo": "Comer, Rezar, Amar", "autor": "Elizabeth Gilbert", "genero": "não-ficção",
                "elementos": ["viagem", "autoconhecimento", "recomeco", "espiritualidade"],
                "hobbies": ["viagens", "reflexao", "autoconhecimento", "culinaria"],
                "tom": ["inspirador", "leve", "esperancoso", "calmo"], "tamanho": "médio",
                "descricao": "Após um divórcio, a autora viaja pela Itália, Índia e Indonésia em uma jornada real de reconexão consigo mesma."
            },
            {
                "titulo": "Garota Exemplar", "autor": "Gillian Flynn", "genero": "mistério/suspense",
                "elementos": ["desaparecimento", "casamento", "segredos", "reviravolta", "manipulacao"],
                "hobbies": ["thrillers", "series", "psicologia"],
                "tom": ["tenso", "sombrio", "envolvente"], "tamanho": "médio",
                "descricao": "Quando Amy desaparece no aniversário de casamento, todas as suspeitas recaem sobre o marido — um thriller cheio de reviravoltas."
            },
            {
                "titulo": "O Silêncio dos Inocentes", "autor": "Thomas Harris", "genero": "terror",
                "elementos": ["serial killer", "investigacao", "psicologia", "fbi", "perseguicao"],
                "hobbies": ["thrillers", "true crime", "series"],
                "tom": ["tenso", "sombrio", "assustador", "envolvente"], "tamanho": "médio",
                "descricao": "A agente Clarice Starling recorre ao brilhante e perturbador Hannibal Lecter para capturar outro assassino em série."
            },
            {
                "titulo": "A Revolução dos Bichos", "autor": "George Orwell", "genero": "distopia",
                "elementos": ["politica", "poder", "revolucao", "satira", "critica social"],
                "hobbies": ["politica", "filosofia", "debates"],
                "tom": ["reflexivo", "ironico", "catartico"], "tamanho": "curto",
                "descricao": "Animais de uma fazenda se rebelam contra os humanos, mas a revolução logo revela novos tiranos — uma sátira política afiada."
            },
            {
                "titulo": "O Conto da Aia", "autor": "Margaret Atwood", "genero": "distopia",
                "elementos": ["opressao", "controle", "mulheres", "regime", "resistencia"],
                "hobbies": ["politica", "series", "sociologia", "debates"],
                "tom": ["sombrio", "tenso", "reflexivo"], "tamanho": "médio",
                "descricao": "Em um regime totalitário, mulheres férteis são reduzidas a 'aias' — um retrato perturbador sobre liberdade e controle."
            },
            {
                "titulo": "Diário de um Banana", "autor": "Jeff Kinney", "genero": "infantojuvenil",
                "elementos": ["escola", "humor", "cotidiano", "amizade"],
                "hobbies": ["humor", "quadrinhos", "filmes"],
                "tom": ["divertido", "leve", "engracado"], "tamanho": "curto",
                "descricao": "Greg narra com humor os perrengues da escola e da família em um diário ilustrado leve e divertido."
            },
            {
                "titulo": "O Sol é Para Todos", "autor": "Harper Lee", "genero": "clássico",
                "elementos": ["justica", "preconceito", "infancia", "moral", "sociedade"],
                "hobbies": ["historia", "reflexao", "debates"],
                "tom": ["reflexivo", "emocionante", "sensivel"], "tamanho": "médio",
                "descricao": "Pela visão da pequena Scout, um advogado defende um homem negro injustamente acusado no sul dos EUA dos anos 1930."
            }
        ]

        # Memória de conversa (usada para refinar e paginar recomendações).
        self.memoria = {
            "ultimo_texto": "",      # último pedido de recomendação
            "ultimo_genero": None,   # último gênero detectado
            "recomendados": []       # títulos já mostrados (para "mais opções")
        }
        # Histórico de humor para detectar uma tendência ao longo da conversa.
        self.historico_humor = []

        # -------------------------------------------------------------------
        # OTIMIZAÇÃO (performance): pré-processa a base e ajusta o TF-IDF
        # UMA ÚNICA VEZ. A cada mensagem, só transformamos a frase do usuário,
        # em vez de reprocessar os 37 livros e refazer o TF-IDF inteiro.
        # -------------------------------------------------------------------
        for livro in self.livros:
            livro["_titulo_norm"] = self.texto_normalizado(livro["titulo"])
            livro["_autor_norm"] = self.texto_normalizado(livro["autor"])
            livro["_elementos_norm"] = {self.texto_normalizado(x) for x in livro["elementos"]}
            livro["_hobbies_norm"] = {self.texto_normalizado(x) for x in livro["hobbies"]}
            livro["_tom_norm"] = {self.texto_normalizado(x) for x in livro["tom"]}

        self._perfis_livros = [self.perfil_livro(livro) for livro in self.livros]
        self.vetor_livros = TfidfVectorizer()
        self.matriz_livros = self.vetor_livros.fit_transform(self._perfis_livros)

        self._base_faq = [self.preprocessar(item["pergunta"]) for item in self.faq]
        self.vetor_faq = TfidfVectorizer()
        self.matriz_faq = self.vetor_faq.fit_transform(self._base_faq)

        # Tabela plana de palavras-chave de gênero (para correspondência aproximada/typos).
        self._kw_genero_flat = {}
        for genero, kws in self.generos_keywords.items():
            for palavra in kws:
                p = remove_acentos(palavra.lower())
                if " " not in p and len(p) >= 4:
                    self._kw_genero_flat.setdefault(p, genero)

    # ----------------------------- Pré-processamento -----------------------------
    def preprocessar(self, texto: str) -> str:
        texto = remove_acentos(texto.lower())
        doc = self.nlp(texto)

        tokens_limpos = []
        for token in doc:
            if token.is_stop or token.is_punct or token.is_space or token.like_num:
                continue
            base = token.lemma_.strip() if token.lemma_ and token.lemma_ != "-PRON-" else token.text.strip()
            base = remove_acentos(base.lower())
            if len(base) <= 1:
                continue
            tokens_limpos.append(base)

        return " ".join(tokens_limpos)

    def texto_normalizado(self, texto: str) -> str:
        texto = remove_acentos(texto.lower())
        texto = re.sub(r"\s+", " ", texto).strip()
        return texto

    # ----------------------------- Detecções por regra -----------------------------
    def detectar_generos(self, texto_normalizado: str):
        generos = set()
        for genero, keywords in self.generos_keywords.items():
            for palavra in keywords:
                if palavra in texto_normalizado:
                    generos.add(genero)
        # Tolerância a erros de digitação (ex.: "fantazia" -> "fantasia").
        if getattr(self, "_kw_genero_flat", None):
            for token in set(re.findall(r"[a-z]+", texto_normalizado)):
                if len(token) < 4:
                    continue
                aprox = difflib.get_close_matches(token, self._kw_genero_flat.keys(), n=1, cutoff=0.84)
                if aprox:
                    generos.add(self._kw_genero_flat[aprox[0]])
        return generos

    def detectar_caracteristicas(self, texto_normalizado: str):
        caracteristicas = set()
        for categoria, keywords in self.keywords_extras.items():
            for palavra in keywords:
                if palavra in texto_normalizado:
                    caracteristicas.add(categoria)
        return caracteristicas

    def detectar_livro_mencionado(self, texto_normalizado: str):
        melhor_parcial = None
        for livro in self.livros:
            titulo = livro.get("_titulo_norm") or self.texto_normalizado(livro["titulo"])
            autor = livro.get("_autor_norm") or self.texto_normalizado(livro["autor"])
            # Correspondência exata de título ou autor tem prioridade.
            if titulo in texto_normalizado or autor in texto_normalizado:
                return livro
            # Correspondência parcial: primeiras palavras do título (ex.: "harry potter").
            palavras_titulo = titulo.split()
            if len(palavras_titulo) >= 2:
                prefixo = " ".join(palavras_titulo[:2])
                if len(prefixo) >= 7 and prefixo in texto_normalizado:
                    melhor_parcial = livro
        if melhor_parcial:
            return melhor_parcial

        # Tolerância a erros: compara o prefixo do título com os bigramas do texto
        # (ex.: "harry poter" ainda encontra "Harry Potter...").
        palavras_texto = texto_normalizado.split()
        bigramas = [" ".join(palavras_texto[i:i + 2]) for i in range(len(palavras_texto) - 1)]
        if bigramas:
            for livro in self.livros:
                palavras_titulo = (livro.get("_titulo_norm") or "").split()
                if len(palavras_titulo) >= 2:
                    prefixo = " ".join(palavras_titulo[:2])
                    if len(prefixo) >= 7 and difflib.get_close_matches(prefixo, bigramas, n=1, cutoff=0.82):
                        return livro
        return None

    def perfil_livro(self, livro):
        partes = [
            livro["titulo"], livro["autor"], livro["genero"],
            " ".join(livro["elementos"]), " ".join(livro["hobbies"]),
            " ".join(livro["tom"]), livro["tamanho"], livro["descricao"]
        ]
        return self.preprocessar(" ".join(partes))

    def bonus_regras(self, livro, texto_normalizado, generos_usuario, caracteristicas_usuario):
        score = 0.0

        if livro["genero"] in generos_usuario:
            score += 0.35

        elementos_norm = livro["_elementos_norm"]
        hobbies_norm = livro["_hobbies_norm"]
        tom_norm = livro["_tom_norm"]

        for termo in elementos_norm:
            if termo in texto_normalizado:
                score += 0.08
        for termo in hobbies_norm:
            if termo in texto_normalizado:
                score += 0.06
        for termo in tom_norm:
            if termo in texto_normalizado:
                score += 0.05

        if "curto" in caracteristicas_usuario and livro["tamanho"] == "curto":
            score += 0.12
        if "longo" in caracteristicas_usuario and livro["tamanho"] == "longo":
            score += 0.12
        if "divertido" in caracteristicas_usuario and any(t in livro["tom"] for t in ["divertido", "leve", "engracado"]):
            score += 0.12
        if "sombrio" in caracteristicas_usuario and any(t in livro["tom"] for t in ["sombrio", "tenso", "assustador", "gotico"]):
            score += 0.12
        if "reflexivo" in caracteristicas_usuario and any(t in livro["tom"] for t in ["reflexivo", "complexo", "inteligente"]):
            score += 0.12
        if "inspirador" in caracteristicas_usuario and any(t in livro["tom"] for t in ["inspirador", "motivacional"]):
            score += 0.12

        return score

    def montar_vibe(self, humor: str, emocao):
        """Monta o 'clima' que vai guiar a recomendação a partir da emoção/humor."""
        if emocao and emocao in VIBES:
            return VIBES[emocao]
        if humor == "negativo":
            return {
                "tons": TONS_CONFORTO, "curto": True, "intros": self.intros_conforto,
                "motivo": "tem um clima leve/reconfortante para levantar o astral",
            }
        return None

    # ----------------------------- REQUISITO 3: híbrido (cosseno) -----------------------------
    def recomendar(self, texto_usuario: str, top_n: int = 3, humor: str = "neutro",
                   excluir_titulos=None, excluir_genero=None, reforcar_acolhimento: bool = False,
                   vibe=None, usar_consulta: bool = True) -> str:
        excluir_titulos = set(excluir_titulos or [])
        texto_normalizado = self.texto_normalizado(texto_usuario)

        generos_usuario = self.detectar_generos(texto_normalizado)
        caracteristicas_usuario = self.detectar_caracteristicas(texto_normalizado)

        if generos_usuario:
            self.memoria["ultimo_genero"] = list(generos_usuario)[0]

        # OTIMIZAÇÃO: a base já está vetorizada; só transformamos a consulta.
        # Em desabafos de puro humor (usar_consulta=False), ignoramos o casamento
        # textual — senão "to com medo" casaria com a descrição de um livro de terror.
        if usar_consulta:
            consulta = self.preprocessar(texto_usuario)
            vetor_consulta = self.vetor_livros.transform([consulta])
            similaridades = cosine_similarity(vetor_consulta, self.matriz_livros).flatten()
        else:
            similaridades = [0.0] * len(self.livros)

        ranking = []
        for i, livro in enumerate(self.livros):
            if livro["titulo"] in excluir_titulos:
                continue
            if excluir_genero and livro["genero"] == excluir_genero:
                continue
            score_total = float(similaridades[i]) + self.bonus_regras(
                livro, texto_normalizado, generos_usuario, caracteristicas_usuario
            )
            # A "vibe" (derivada do humor/emoção) prioriza livros com o clima certo
            # — ex.: tristeza puxa leituras reconfortantes; tédio puxa vira-páginas.
            if vibe:
                if livro["_tom_norm"] & vibe["tons"]:
                    score_total += 0.30
                if vibe.get("curto") and livro["tamanho"] == "curto":
                    score_total += 0.10
            # Em desabafos (sem consulta textual), um leve sorteio dá variedade às
            # sugestões entre conversas, sem deixar livros fora do clima subirem.
            if not usar_consulta:
                score_total += random.uniform(0, 0.06)
            ranking.append((score_total, livro))

        ranking.sort(key=lambda x: x[0], reverse=True)
        melhores = ranking[:top_n]

        # Memória: guarda o contexto e os títulos já mostrados (para "mais opções").
        self.memoria["ultimo_texto"] = texto_usuario
        self.memoria["ultima_vibe"] = vibe
        self.memoria["ultimo_usar_consulta"] = usar_consulta
        mostrados = [livro["titulo"] for _, livro in melhores]
        self.memoria["recomendados"] = list(excluir_titulos) + mostrados if excluir_titulos else mostrados

        if not melhores:
            return ("Acho que já te mostrei as melhores opções para isso. 😊\n"
                    "Me dá um novo critério (gênero, tema ou clima) que eu busco mais!")

        # Com uma vibe definida, sempre recomendamos algo no clima certo (mais assertivo).
        if melhores[0][0] < 0.08 and not vibe:
            return (
                "Não consegui identificar muito bem seu gosto ainda. Tente algo mais específico, por exemplo:\n"
                "- 'quero fantasia com magia e amizade'\n"
                "- 'gosto de suspense policial e investigação'\n"
                "- 'procuro ficção científica com política e filosofia'"
            )

        if vibe:
            resposta = [random.choice(vibe["intros"]) + "\n"]
        elif humor == "positivo":
            resposta = [random.choice(self.intros_positivos) + "\n"]
        else:
            resposta = [random.choice(self.intros_neutros) + "\n"]

        for posicao, (score, livro) in enumerate(melhores, start=1):
            motivos = []
            if livro["genero"] in generos_usuario:
                motivos.append(f"combina com o gênero {livro['genero']}")
            elementos_citados = [e for e in livro["elementos"] if self.texto_normalizado(e) in texto_normalizado]
            hobbies_citados = [h for h in livro["hobbies"] if self.texto_normalizado(h) in texto_normalizado]

            if elementos_citados:
                motivos.append("tem elementos como " + ", ".join(elementos_citados[:3]))
            if hobbies_citados:
                motivos.append("conversa com seus interesses em " + ", ".join(hobbies_citados[:2]))
            if vibe and (livro["_tom_norm"] & vibe["tons"]):
                motivos.append(vibe["motivo"])
            if "curto" in caracteristicas_usuario and livro["tamanho"] == "curto":
                motivos.append("é uma opção curta")
            if "longo" in caracteristicas_usuario and livro["tamanho"] == "longo":
                motivos.append("é uma leitura mais longa")
            if "divertido" in caracteristicas_usuario and any(t in livro["tom"] for t in ["divertido", "leve", "engracado"]):
                motivos.append("tem um tom leve/divertido")
            if "sombrio" in caracteristicas_usuario and any(t in livro["tom"] for t in ["sombrio", "tenso", "assustador"]):
                motivos.append("tem um clima mais sombrio")
            if "reflexivo" in caracteristicas_usuario and any(t in livro["tom"] for t in ["reflexivo", "complexo", "inteligente"]):
                motivos.append("traz uma pegada mais reflexiva")

            if not motivos:
                motivos.append("tem alta similaridade com a sua descrição")

            resposta.append(
                f"{posicao}) {livro['titulo']} — {livro['autor']}\n"
                f"   Gênero: {livro['genero']}\n"
                f"   Motivo: {'; '.join(motivos)}.\n"
                f"   Resumo: {livro['descricao']}\n"
            )

        if humor == "negativo":
            fecho = "Se quiser desabafar um pouco mais, eu tô por aqui. 💛"
            if reforcar_acolhimento:
                fecho = ("Percebi que o papo tá meio pesado faz um tempinho. Tô aqui de verdade pra te ouvir. 💛\n"
                         + fecho)
            resposta.append(fecho)
        else:
            resposta.append("Se quiser, posso refinar. Ex.: 'algo mais curto', 'mais sombrio', 'com romance', 'mais opções'.")

        return "\n".join(resposta)

    def recomendar_semelhantes(self, livro_base, top_n: int = 3) -> str:
        # OTIMIZAÇÃO: o perfil do livro-base já está na matriz pré-calculada.
        try:
            idx = self.livros.index(livro_base)
            similaridades = cosine_similarity(self.matriz_livros[idx], self.matriz_livros).flatten()
        except ValueError:
            vetor_consulta = self.vetor_livros.transform([self.perfil_livro(livro_base)])
            similaridades = cosine_similarity(vetor_consulta, self.matriz_livros).flatten()

        ranking = []
        for i, livro in enumerate(self.livros):
            if livro["titulo"] == livro_base["titulo"]:
                continue
            score = float(similaridades[i])
            if livro["genero"] == livro_base["genero"]:
                score += 0.25
            ranking.append((score, livro))

        ranking.sort(key=lambda x: x[0], reverse=True)
        melhores = ranking[:top_n]

        resposta = [f"Se você gostou de {livro_base['titulo']}, estas são boas opções parecidas:\n"]
        for posicao, (score, livro) in enumerate(melhores, start=1):
            resposta.append(
                f"{posicao}) {livro['titulo']} — {livro['autor']}\n"
                f"   Gênero: {livro['genero']}\n"
                f"   Resumo: {livro['descricao']}\n"
            )
        return "\n".join(resposta)

    def responder_faq(self, texto_usuario: str, limiar: float = 0.12):
        # OTIMIZAÇÃO: o FAQ já está vetorizado; só transformamos a consulta.
        consulta = self.preprocessar(texto_usuario)
        similaridades = cosine_similarity(self.vetor_faq.transform([consulta]), self.matriz_faq).flatten()

        indice = int(similaridades.argmax())
        if similaridades[indice] >= limiar:
            return self.faq[indice]["resposta"]
        return None

    def detalhes_livro(self, livro):
        return (
            f"{livro['titulo']} — {livro['autor']}\n"
            f"Gênero: {livro['genero']}\n"
            f"Elementos principais: {', '.join(livro['elementos'])}\n"
            f"Tom: {', '.join(livro['tom'])}\n"
            f"Tamanho aproximado: {livro['tamanho']}\n"
            f"Resumo: {livro['descricao']}"
        )

    def eh_pergunta_faq_direta(self, texto_limpo: str):
        if "quais generos" in texto_limpo or ("generos" in texto_limpo and "recomenda" in texto_limpo):
            return self.faq[0]["resposta"]
        if "como voce funciona" in texto_limpo or "como funciona" in texto_limpo:
            return self.faq[1]["resposta"]
        if "exemplos de perguntas" in texto_limpo or "exemplos" in texto_limpo:
            return self.faq[2]["resposta"]
        if "diferenca" in texto_limpo and "fantasia" in texto_limpo and ("ficcao cientifica" in texto_limpo or "ficção científica" in texto_limpo):
            return self.faq[3]["resposta"]
        if "comecar a ler" in texto_limpo or "iniciante" in texto_limpo:
            return self.faq[4]["resposta"]
        if ("voz" in texto_limpo or "falar" in texto_limpo or "microfone" in texto_limpo) and ("voce" in texto_limpo or "entende" in texto_limpo or "como" in texto_limpo):
            return self.faq[5]["resposta"]
        return None

    def tem_sinal_de_recomendacao(self, texto_limpo: str):
        verbos = ["quero", "gosto", "procuro", "indique", "indicar", "recomende", "recomendar",
                  "sugira", "sugestao", "sugestão", "parecido", "queria", "busco", "buscando"]
        if any(v in texto_limpo for v in verbos):
            return True
        if self.detectar_generos(texto_limpo):
            return True
        if self.detectar_caracteristicas(texto_limpo):
            return True

        palavras_dominios = [
            "magia", "amizade", "detetive", "investigacao", "investigação", "amor",
            "politica", "política", "filosofia", "crime", "aventura", "hacker",
            "espaco", "espaço", "humor", "mitologia", "sociedade", "livro", "ler",
            "leitura", "vampiro", "terror", "habito", "historia"
        ]
        return any(p in texto_limpo for p in palavras_dominios)

    # Refinamentos da conversa: ajustar a última recomendação ("mais curto"),
    # pedir mais opções ("mais opções", "outro") ou tirar um gênero ("menos fantasia").
    MODIFICADORES_REFINO = {
        "curto": "curto leve rapido", "curta": "curto leve", "menor": "curto leve", "rapido": "curto leve",
        "longo": "longo denso complexo", "longa": "longo denso", "grande": "longo denso",
        "sombrio": "sombrio tenso pesado", "sombria": "sombrio tenso", "pesado": "sombrio tenso", "dark": "sombrio tenso",
        "leve": "leve divertido", "divertido": "leve divertido humor", "divertida": "leve divertido",
        "engracado": "humor divertido", "reflexivo": "reflexivo profundo filosofia", "profundo": "reflexivo filosofia",
        "romance": "romance amor", "romantico": "romance amor", "aventura": "aventura jornada",
        "terror": "terror medo sombrio", "inspirador": "inspirador motivacional"
    }

    def detectar_refinamento(self, texto_limpo: str):
        palavras = texto_limpo.split()

        gatilhos_mais = [
            "mais opcoes", "mais opcao", "outras opcoes", "outra opcao", "mais livros",
            "tem mais", "mais um", "me da outro", "mais sugestoes", "outras sugestoes",
            "mostra mais", "tem outro", "tem outra"
        ]
        if any(g in texto_limpo for g in gatilhos_mais) or texto_limpo in {"mais", "outro", "outra", "outros", "outras"}:
            return {"tipo": "mais_opcoes"}

        # "menos <gênero>": remove um gênero do resultado.
        if "menos" in palavras:
            generos = self.detectar_generos(texto_limpo)
            if generos:
                return {"tipo": "ajustar", "keywords": "", "excluir_genero": list(generos)[0]}

        # "mais <modificador>" ou mensagem curta de ajuste, sem verbo de novo pedido.
        tem_verbo = any(v in palavras for v in
                        ["quero", "queria", "gosto", "procuro", "busco", "indique", "recomende", "sugira"])
        if not tem_verbo and ("mais" in palavras or len(palavras) <= 3):
            achou = [kw for chave, kw in self.MODIFICADORES_REFINO.items() if chave in palavras]
            if achou:
                return {"tipo": "ajustar", "keywords": " ".join(achou)}
        return None

    def texto_exemplos(self):
        return (
            "Exemplos do que você pode dizer (digitando ou no 🎤 Falar):\n"
            "- Quero fantasia com magia e amizade.\n"
            "- Gosto de ficção científica com política e filosofia.\n"
            "- Procuro um livro curto e divertido.\n"
            "- Quero suspense com detetive.\n"
            "- Tô meio pra baixo hoje...\n"
            "- Fale sobre Duna.\n"
            "- Quero algo parecido com Harry Potter."
        )

    def responder(self, texto_usuario: str) -> str:
    
        sent = self.analisador.analisar(texto_usuario)  # mensagem recebida vai para a função analisar.
        self.ultimo_sentimento = sent
        humor = sent["label"]
        emocao = sent.get("emocao")

        # Tendência de humor: se o usuário vem negativo há um tempo, reforçamos o acolhimento.
        self.historico_humor.append(humor)
        self.historico_humor = self.historico_humor[-5:]
        reforco = self.historico_humor[-3:].count("negativo") >= 2

        # "Clima" das recomendações (a partir da emoção/humor detectados).
        vibe = self.montar_vibe(humor, emocao)

        limpo = self.texto_normalizado(texto_usuario)

        # Mensagem vazia ou só com emoji
        if not limpo:
            if vibe:
                return self.recomendar(texto_usuario, humor=humor, vibe=vibe,
                                       reforcar_acolhimento=reforco, usar_consulta=False)
            if humor == "positivo":
                return random.choice(self.acks_positivos) + " " + random.choice(self.respostas_neutras_sem_sinal)
            return "Pode digitar ou falar (🎤) uma preferência: gênero, tema, autor ou um livro que você gostou."

        palavras = limpo.split()

        # Despedida
        if any(d in limpo for d in self.despedidas) and len(palavras) <= 3:
            return random.choice(self.despedidas_saida)

        # Saudação curta (randômica)
        if any(s in limpo for s in self.saudações_entrada) and len(palavras) <= 2:
            return random.choice(self.saudações_saida)

        # Ajuda / exemplos
        if "exemplo" in limpo or "ajuda" in limpo or "como usar" in limpo:
            return self.texto_exemplos()

        # FAQ direta
        faq_direta = self.eh_pergunta_faq_direta(limpo)
        if faq_direta:
            return faq_direta

        # Pedido de detalhes / semelhantes sobre um livro específico
        livro_mencionado = self.detectar_livro_mencionado(limpo)
        if livro_mencionado and any(p in limpo for p in ["fale sobre", "detalhe", "resumo", "sobre", "quem escreveu"]):
            return self.detalhes_livro(livro_mencionado)
        if livro_mencionado and any(p in limpo for p in ["parecido", "parecida", "semelhante"]):
            return self.recomendar_semelhantes(livro_mencionado)

        if self.memoria.get("ultimo_texto"):
            refino = self.detectar_refinamento(limpo)
            if refino:
                # A mensagem de refino ("mais opções") não tem clima próprio:
                # reaproveitamos a vibe/contexto da recomendação anterior.
                vibe_efetiva = vibe or self.memoria.get("ultima_vibe")
                if refino["tipo"] == "mais_opcoes":
                    return self.recomendar(
                        self.memoria["ultimo_texto"], humor=humor, vibe=vibe_efetiva,
                        excluir_titulos=set(self.memoria.get("recomendados", [])),
                        reforcar_acolhimento=reforco,
                        usar_consulta=self.memoria.get("ultimo_usar_consulta", True)
                    )
                novo_texto = (self.memoria["ultimo_texto"] + " " + refino.get("keywords", "")).strip()
                return self.recomendar(
                    novo_texto, humor=humor, vibe=vibe_efetiva,
                    excluir_genero=refino.get("excluir_genero"),
                    reforcar_acolhimento=reforco
                )

        # Pedido explícito de recomendação (usa o humor/clima para ajustar tom e seleção)
        if self.tem_sinal_de_recomendacao(limpo):
            return self.recomendar(texto_usuario, humor=humor, vibe=vibe, reforcar_acolhimento=reforco)

        # Há um clima emocional (negativo, ou emoções como tédio/empolgação): recomenda
        # no tom certo mesmo sem pedido explícito deixa o bot mais assertivo.
        # usar_consulta=False: é um desabafo, então rankeamos pelo clima, não pelo texto.
        if vibe:
            return self.recomendar(texto_usuario, humor=humor, vibe=vibe,
                                   reforcar_acolhimento=reforco, usar_consulta=False)

        # Positivo sem sinal e sem emoção: acolhe o ânimo e pede preferências
        if humor == "positivo":
            return random.choice(self.acks_positivos) + " " + random.choice(self.respostas_neutras_sem_sinal)

        # Neutro sem sinal: tenta FAQ; senão pede mais informação
        faq = self.responder_faq(texto_usuario)
        if faq:
            return faq
        return random.choice(self.respostas_neutras_sem_sinal)


# ===========================================================================
# REQUISITO 1 (GUI) + REQUISITO 5 (voz)
# ===========================================================================
class InterfaceChatbot:
    def __init__(self, root):
        self.root = root
        self.root.title("BookBot PLN - Recomendação de Livros")
        self.root.geometry("960x680")
        self.root.minsize(860, 600)

        self.chatbot = ChatbotLivros()

        # Estado da voz
        self.tts_ativo = tk.BooleanVar(value=False)
        self._tts_lock = threading.Lock()
        self._ouvindo = False

        self.criar_widgets()
        self.mensagem_inicial()

    # ----------------------------- Widgets -----------------------------
    def criar_widgets(self):
        frame_topo = ttk.Frame(self.root, padding=10)
        frame_topo.pack(fill="x")

        titulo = ttk.Label(
            frame_topo,
            text="Chatbot Híbrido de Recomendação de Livros",
            font=("Arial", 16, "bold")
        )
        titulo.pack(anchor="w")

        subtitulo = ttk.Label(
            frame_topo,
            text="Digite ou fale gostos, gêneros, temas, ou peça detalhes de um livro. Eu também percebo o seu humor.",
            font=("Arial", 10)
        )
        subtitulo.pack(anchor="w", pady=(4, 0))

        # Barra de status (humor + voz)
        frame_status = ttk.Frame(self.root, padding=(10, 0))
        frame_status.pack(fill="x")

        self.label_humor = ttk.Label(frame_status, text="Humor detectado: 😐 neutro", font=("Arial", 10, "bold"))
        self.label_humor.pack(side="left")

        self.label_digitando = ttk.Label(frame_status, text="", font=("Arial", 9, "italic"), foreground="#2E7D32")
        self.label_digitando.pack(side="left", padx=20)

        self.label_voz = ttk.Label(frame_status, text="", font=("Arial", 9), foreground="#555")
        self.label_voz.pack(side="right")

        # Área do chat
        self.area_chat = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, font=("Arial", 11), padx=10, pady=10
        )
        self.area_chat.pack(fill="both", expand=True, padx=10, pady=10)
        self.area_chat.config(state="disabled")
        # Cores diferentes para identificar quem fala.
        self.area_chat.tag_config("autor_voce", foreground="#1565C0", font=("Arial", 11, "bold"))
        self.area_chat.tag_config("autor_bot", foreground="#2E7D32", font=("Arial", 11, "bold"))
        self.area_chat.tag_config("texto", foreground="#1A1A1A")

        # Entrada + botões
        frame_input = ttk.Frame(self.root, padding=10)
        frame_input.pack(fill="x")

        self.entrada = ttk.Entry(frame_input, font=("Arial", 12))
        self.entrada.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entrada.bind("<Return>", self.enviar_mensagem)

        botao_enviar = ttk.Button(frame_input, text="Enviar", command=self.enviar_mensagem)
        botao_enviar.pack(side="left", padx=(0, 8))

        self.botao_voz = ttk.Button(frame_input, text="🎤 Falar", command=self.ouvir_voz)
        self.botao_voz.pack(side="left", padx=(0, 8))

        self.check_tts = ttk.Checkbutton(frame_input, text="🔊 Falar respostas", variable=self.tts_ativo)
        self.check_tts.pack(side="left", padx=(0, 8))

        botao_limpar = ttk.Button(frame_input, text="Limpar", command=self.limpar_chat)
        botao_limpar.pack(side="left", padx=(0, 8))

        botao_exemplos = ttk.Button(frame_input, text="Exemplos", command=self.mostrar_exemplos)
        botao_exemplos.pack(side="left")

        # Ajusta disponibilidade da voz conforme bibliotecas instaladas
        avisos = []
        if not VOZ_ENTRADA_OK:
            self.botao_voz.config(state="disabled")
            avisos.append("entrada de voz indisponível (instale SpeechRecognition + PyAudio)")
        if not VOZ_SAIDA_OK:
            self.check_tts.config(state="disabled")
            avisos.append("fala indisponível (instale pyttsx3)")
        if avisos:
            self.label_voz.config(text=" | ".join(avisos))
        else:
            self.label_voz.config(text="voz pronta 🎙️")

    # ----------------------------- Mensagens do chat -----------------------------
    def adicionar_mensagem(self, autor, mensagem, autor_tag="autor_bot"):
        self.area_chat.config(state="normal")
        self.area_chat.insert(tk.END, f"{autor}:\n", autor_tag)
        self.area_chat.insert(tk.END, f"{mensagem}\n\n", "texto")
        self.area_chat.config(state="disabled")
        self.area_chat.see(tk.END)

    def mensagem_inicial(self):
        extra = ""
        if VOZ_ENTRADA_OK or VOZ_SAIDA_OK:
            extra = "\n\nDica: use o 🎤 para falar comigo e marque 🔊 para eu ler as respostas em voz alta."
        msg = (
            "Olá! Eu recomendo livros com base no que você gosta — e percebo o seu humor para ajustar o tom.\n\n"
            "Experimente:\n"
            "• gosto de fantasia, magia e amizade\n"
            "• quero ficção científica com política e filosofia\n"
            "• procuro um livro curto e divertido\n"
            "• tô meio pra baixo hoje...\n"
            "• fale sobre Duna" + extra
        )
        self.adicionar_mensagem("BookBot", msg)

    def atualizar_humor(self):
        sent = self.chatbot.ultimo_sentimento
        cores = {"positivo": "#2E7D32", "neutro": "#B8860B", "negativo": "#C62828"}
        extra = f" · {sent['emocao']}" if sent.get("emocao") else ""
        self.label_humor.config(
            text=f"Humor detectado: {sent['emoji']} {sent['label']}{extra} (score {sent['compound']:+.2f})",
            foreground=cores.get(sent["label"], "#000000")
        )

    def enviar_mensagem(self, event=None):
        texto = self.entrada.get().strip()
        if not texto:
            messagebox.showinfo("Aviso", "Digite ou fale uma mensagem para continuar.")
            return

        self.adicionar_mensagem("Você", texto, autor_tag="autor_voce")
        self.entrada.delete(0, tk.END)

        self.label_digitando.config(text="BookBot está digitando…")
        self.root.update_idletasks()

        resposta = self.chatbot.responder(texto)

        self.label_digitando.config(text="")
        self.atualizar_humor()
        self.adicionar_mensagem("BookBot", resposta)

        if self.tts_ativo.get() and VOZ_SAIDA_OK:
            self.falar(resposta)

    def limpar_chat(self):
        self.area_chat.config(state="normal")
        self.area_chat.delete("1.0", tk.END)
        self.area_chat.config(state="disabled")
        self.label_humor.config(text="Humor detectado: 😐 neutro", foreground="#000000")
        self.label_digitando.config(text="")
        # Reinicia a memória de conversa e o histórico de humor.
        self.chatbot.memoria = {"ultimo_texto": "", "ultimo_genero": None, "recomendados": []}
        self.chatbot.historico_humor = []
        self.mensagem_inicial()

    def mostrar_exemplos(self):
        self.adicionar_mensagem("BookBot", self.chatbot.texto_exemplos())

    # ----------------------------- REQUISITO 5: voz -----------------------------
    def ouvir_voz(self):
        """Captura a fala do usuário em uma thread (não trava a interface)."""
        if not VOZ_ENTRADA_OK or self._ouvindo:
            return
        self._ouvindo = True
        self.botao_voz.config(state="disabled")
        self.label_voz.config(text="Ajustando ruído do ambiente...")
        threading.Thread(target=self._ouvir_thread, daemon=True).start()

    def _ouvir_thread(self):
        reconhecedor = sr.Recognizer()
        try:
            with sr.Microphone() as fonte:
                reconhecedor.adjust_for_ambient_noise(fonte, duration=0.6)
                self.root.after(0, lambda: self.label_voz.config(text="🎤 Ouvindo... pode falar"))
                audio = reconhecedor.listen(fonte, timeout=6, phrase_time_limit=12)
            self.root.after(0, lambda: self.label_voz.config(text="Processando o áudio..."))
            texto = reconhecedor.recognize_google(audio, language="pt-BR")
            self.root.after(0, lambda: self._preencher_e_enviar(texto))
        except sr.WaitTimeoutError:
            self.root.after(0, lambda: self.label_voz.config(text="Não ouvi nada. Tente de novo."))
        except sr.UnknownValueError:
            self.root.after(0, lambda: self.label_voz.config(text="Não entendi o que foi dito."))
        except sr.RequestError:
            self.root.after(0, lambda: self.label_voz.config(text="Sem conexão com o serviço de voz (precisa de internet)."))
        except Exception as erro:
            mensagem = str(erro)
            self.root.after(0, lambda: self.label_voz.config(text=f"Erro de voz: {mensagem}"))
        finally:
            self._ouvindo = False
            self.root.after(0, lambda: self.botao_voz.config(state="normal"))

    def _preencher_e_enviar(self, texto):
        self.label_voz.config(text="voz pronta 🎙️")
        self.entrada.delete(0, tk.END)
        self.entrada.insert(0, texto)
        self.enviar_mensagem()

    def falar(self, texto):
        """Lê a resposta em voz alta (TTS) em uma thread separada."""
        if not VOZ_SAIDA_OK:
            return
        threading.Thread(target=self._falar_thread, args=(texto,), daemon=True).start()

    def _falar_thread(self, texto):
        # Evita falas sobrepostas
        if not self._tts_lock.acquire(blocking=False):
            return
        try:
            engine = pyttsx3.init()
            try:
                for voz in engine.getProperty("voices"):
                    nome = (voz.name or "").lower()
                    idv = (voz.id or "").lower()
                    if "pt" in idv or "portug" in nome or "brazil" in nome or "maria" in nome or "daniel" in nome:
                        engine.setProperty("voice", voz.id)
                        break
            except Exception:
                pass
            engine.setProperty("rate", 180)
            # Lê uma versão enxuta (sem excesso de quebras de linha)
            fala = re.sub(r"\s+", " ", texto).strip()
            engine.say(fala)
            engine.runAndWait()
        except Exception:
            pass
        finally:
            self._tts_lock.release()


if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass
    app = InterfaceChatbot(root)
    root.mainloop()
