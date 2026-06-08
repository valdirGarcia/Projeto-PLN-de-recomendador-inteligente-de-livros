## ✨ Sobre o projeto

O **BookBot** é um chatbot de **recomendação de livros** desenvolvido como projeto da
disciplina de **Processamento de Linguagem Natural (PLN)** na Fatec.

Ele vai além de um buscador comum: além de entender o que você gosta (gênero, tema,
autor), ele faz **análise de sentimento** da sua mensagem e **adapta o tom e as
recomendações ao seu humor**. Se o seu dia foi ruim, ele te acolhe e sugere leituras
leves; se você está entediado, ele indica vira-páginas; se está empolgado, manda
aventuras. 💛

> 🎓 Projeto acadêmico que combina **regras + recuperação por similaridade (TF-IDF)
> + análise de sentimento por léxico + voz**, tudo em português.

<!--
  📸 DICA: grave um GIF curto usando o chat e coloque aqui para a vitrine ficar completa!
  Sugestão de ferramentas: ScreenToGif (Windows) ou LICEcap.
  Depois adicione:  ![Demonstração do BookBot](docs/demo.gif)
-->

---

## 🚀 Funcionalidades

- 🖥️ **Interface gráfica** intuitiva (Tkinter), com cores por interlocutor e indicador de "digitando…".
- 📚 **Base de conhecimento própria** com **48 livros** catalogados (gênero, elementos, tom, resumo).
- 🧠 **Chat híbrido**: combina respostas **randômicas** (variadas) com **similaridade de cosseno (TF-IDF)**.
- ❤️ **Análise de sentimento + emoção**: detecta humor (positivo/neutro/negativo) e **7 emoções**
  (tristeza, ansiedade, raiva, tédio, cansaço, medo, empolgação) e adapta as sugestões a cada uma.
- 🎤 **Voz**: fale com o bot (reconhecimento de fala em pt-BR) e ouça as respostas (texto-para-fala).
- 💬 **Conversa com contexto**: "mais opções", "mais curto", "menos fantasia" refinam a recomendação anterior.
- 🔍 **Tolerância a erros de digitação** em gêneros e títulos ("fantazia", "harry poter").
- ⚡ **Rápido**: pré-processamento e TF-IDF calculados uma única vez → resposta em ~2 ms.

---

## 🛠️ Tecnologias

| Categoria | Ferramenta |
|---|---|
| Linguagem | Python 3.11 |
| PLN | spaCy (`pt_core_news_sm`) — tokenização, stopwords, lematização |
| Similaridade | scikit-learn — `TfidfVectorizer` + `cosine_similarity` |
| Interface | Tkinter |
| Voz (entrada) | SpeechRecognition + PyAudio (API Google, pt-BR) |
| Voz (saída) | pyttsx3 (offline) |

---

## ⚙️ Como executar

```bash
# 1. Instale as dependências
pip install -r requirements_chatbot_livros.txt

# 2. Baixe o modelo de português do spaCy
python -m spacy download pt_core_news_sm

# 3. Rode o chatbot
python chatbot_livros.py
```

> 💡 As bibliotecas de voz são **opcionais**: se não forem instaladas, o chat por
> texto continua 100% funcional e os botões de voz ficam desativados.
> No Windows, se o `pip install PyAudio` falhar, use: `pip install pipwin && pipwin install pyaudio`.

---

## 💬 Exemplos de uso

```
você> quero fantasia com magia e amizade
bot > Olha o que separei pra você:
      1) Harry Potter e a Pedra Filosofal — J. K. Rowling ...

você> meu dia foi uma droga
bot > Às vezes uma boa história ajuda a aliviar. Veja estas sugestões reconfortantes:
      1) As Crônicas de Nárnia ...   (clima leve para levantar o astral)

você> to entediado
bot > Bora espantar o tédio com uns livros bem envolventes:
      1) ...   (vira-páginas)

você> mais opções
bot > (mostra novas sugestões, sem repetir as anteriores)
```

| Você diz… | O bot entende | E recomenda… |
|---|---|---|
| "gosto de suspense com detetive" | gênero mistério | thrillers/investigação |
| "meu dia foi uma droga" | humor negativo | leituras leves/reconfortantes |
| "to muito ansioso" | emoção: ansiedade | leituras calmas |
| "to super animado!" | emoção: empolgação | aventuras |
| "fale sobre Duna" | livro citado | detalhes do livro |
| "algo parecido com Harry Potter" | livro citado | livros semelhantes |

---

## 🧩 Como funciona (arquitetura)

```
Usuário (texto ou voz 🎤)
        │
        ▼
┌───────────────────────────────────────────────┐
│ AnalisadorSentimento  → humor + emoção          │  (léxico em PT)
├───────────────────────────────────────────────┤
│ ChatbotLivros.responder()                       │
│   • regras (saudação, FAQ, livro citado...)     │
│   • refinamento ("mais opções", "mais curto")   │
│   • recomendar() → TF-IDF + cosseno + "vibe"     │  (híbrido)
├───────────────────────────────────────────────┤
│ InterfaceChatbot  → janela + cores + voz (TTS)  │
└───────────────────────────────────────────────┘
```

O **"clima" (vibe)** derivado da emoção dá um bônus aos livros com o tom certo
(ex.: tristeza → leves/reconfortantes; tédio → envolventes). Em desabafos, o ranking
é guiado pelo clima — e não pelo texto — para evitar, por exemplo, recomendar terror
a quem disse "estou com medo".

---

## 📂 Estrutura do projeto

```
.
├── chatbot_livros.py              # Código principal (GUI + chatbot + sentimento + voz)
├── requirements_chatbot_livros.txt# Dependências
├── README.md                      # Este arquivo
```

## 🎯 Requisitos atendidos

Este projeto foi construído sobre 5 requisitos de PLN:

| # | Requisito | Como foi atendido |
|---|---|---|
| 1 | Interface gráfica (GUI) | Janela em Tkinter |
| 2 | Base de conhecimento própria | 48 livros + pré-processamento com spaCy |
| 3 | Chat híbrido (randômico + cosseno) | `random.choice` + TF-IDF/cosseno |
| 4 | Adaptação ao humor (análise de sentimento) | Léxico próprio + detecção de 7 emoções |
| 5 | Funcionalidade extra | Voz (reconhecimento de fala + síntese de voz) |

---

## 🌱 Melhorias futuras

- [ ] Modelo de sentimento via **HuggingFace** (toggle opcional)
- [ ] Detecção automática de idioma
- [ ] Base de livros externa em **JSON / banco de dados**
- [ ] Testes automatizados
- [ ] Histórico/preferências do usuário persistidos

---

## 👤 Autor

Projeto desenvolvido por **Valdir** para a disciplina de PLN — Fatec.
