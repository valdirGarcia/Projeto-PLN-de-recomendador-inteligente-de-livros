============================================================
  Chatbot Híbrido de Recomendação de Livros  (Projeto de PLN)
============================================================

Um chatbot, com interface gráfica, que recomenda livros conversando com o
usuário, percebe o humor dele e adapta as respostas — e ainda aceita comandos
de voz e fala as respostas em voz alta.


------------------------------------------------------------
COMO OS 5 REQUISITOS DO PROFESSOR SÃO ATENDIDOS
------------------------------------------------------------
1) Interface com o usuário (GUI)
   -> Janela em Tkinter (classe InterfaceChatbot): área de conversa, campo de
      texto, botões de Enviar, "🎤 Falar", "🔊 Falar respostas", Limpar e
      Exemplos, além de uma barra que mostra o humor detectado.

2) Base de conhecimento "própria" (com tratamentos para otimizar o texto)
   -> 48 livros catalogados manualmente (self.livros), com gênero, elementos,
      hobbies, tom, tamanho e resumo, cobrindo vários gêneros e humores.
   -> Pré-processamento com spaCy: minúsculas, remoção de acentos, remoção de
      stopwords/pontuação/números e lematização (preprocessar()).

3) Chat híbrido (randômico + cossenos)
   -> RANDÔMICO: saudações, despedidas, introduções e respostas variadas são
      sorteadas com random.choice (vários bancos de frases).
   -> COSSENO: TF-IDF (TfidfVectorizer) + similaridade de cosseno comparam o
      pedido do usuário com o perfil de cada livro e com as perguntas do FAQ.

4) Chat que se adequa ao humor do cliente (análise de sentimento)
   -> AnalisadorSentimento: léxico próprio em português (positivas/negativas, com
      gírias) e tratamento de NEGAÇÃO ("não gostei"), INTENSIFICADORES ("muito"),
      EMOJIS e expressões de duas palavras ("pra baixo", "uma droga").
   -> Classifica em positivo / neutro / negativo E detecta a EMOÇÃO específica
      (tristeza, ansiedade, raiva, tédio, cansaço, medo, empolgação).
   -> ADAPTA a resposta ao "clima" (ver VIBES): tristeza/ansiedade puxam leituras
      leves e calmas para confortar; tédio puxa vira-páginas; empolgação puxa
      aventuras. Se o usuário está negativo há várias mensagens, reforça o acolhimento.

5) Funcionalidade extra (som)
   -> Entrada por voz (STT): botão "🎤 Falar" usa SpeechRecognition + Google
      (pt-BR) para transcrever a fala (igual ao asr_online.py da aula).
   -> Saída por voz (TTS): marque "🔊 Falar respostas" para o bot ler as
      respostas em voz alta (pyttsx3, offline no Windows).


------------------------------------------------------------
COMO EXECUTAR
------------------------------------------------------------
1. Instale as bibliotecas:
   pip install -r requirements_chatbot_livros.txt

2. Baixe o modelo de português do spaCy:
   python -m spacy download pt_core_news_sm
   (Se não baixar, o chat ainda funciona com um pipeline básico de português.)

3. Rode o arquivo principal:
   python chatbot_livros.py


------------------------------------------------------------
OBSERVAÇÕES SOBRE A VOZ (requisito 5)
------------------------------------------------------------
- A entrada por voz (microfone) precisa do PyAudio e de conexão com a internet
  (o reconhecimento usa a API do Google, em pt-BR).
- A saída por voz (pyttsx3) funciona offline no Windows (usa as vozes do SAPI5).
- Se as bibliotecas de voz NÃO estiverem instaladas, o programa abre normalmente
  e apenas desativa os botões de voz — o chat por texto continua 100% funcional.

- Se o "pip install PyAudio" falhar no Windows, tente:
      pip install pipwin
      pipwin install pyaudio
  (ou baixe o wheel correspondente à sua versão de Python).


------------------------------------------------------------
DIFERENCIAIS / OTIMIZAÇÕES IMPLEMENTADAS
------------------------------------------------------------
Performance:
- A base de livros é pré-processada (spaCy) e vetorizada (TF-IDF) UMA única vez,
  no início. A cada mensagem, só a frase do usuário é transformada — antes o bot
  reprocessava todos os livros e refazia o TF-IDF inteiro a cada mensagem.
- O modelo spaCy é carregado sem os componentes 'parser' e 'ner' (não usados).
- Campos dos livros são normalizados uma vez e reaproveitados.
  Resultado: resposta em ~2 ms por mensagem.

Recomendação por humor/emoção:
- Detecta a emoção (tristeza, ansiedade, raiva, tédio, cansaço, medo, empolgação)
  e escolhe o "clima" dos livros (ver VIBES) — ex.: "to entediado" -> vira-páginas;
  "to ansioso" -> leituras calmas; "to animado" -> aventuras.
- Em desabafos, o ranking é guiado pelo clima (não pelo texto), senão "to com medo"
  acabaria casando com a descrição de um livro de terror.
- Mais assertivo: havendo clima emocional, sempre recomenda algo (não fica só
  pedindo mais detalhes).

Conversa mais inteligente (usa memória do diálogo):
- "mais opções" / "outro" -> mostra novas sugestões sem repetir as já dadas.
- "mais curto", "mais sombrio", "mais leve" -> refina a recomendação anterior.
- "menos fantasia" -> remove um gênero do resultado.
- Tendência de humor: se o usuário está negativo há várias mensagens, o bot
  reforça o acolhimento.

Robustez e interface:
- Tolerância a erros de digitação em gêneros e títulos ("fantazia", "harry poter").
- Cores diferentes para "Você" e "BookBot", indicador de humor colorido
  (verde/amarelo/vermelho) e aviso "BookBot está digitando…".


------------------------------------------------------------
EXEMPLOS PARA TESTAR
------------------------------------------------------------
- Quero fantasia com magia e amizade.
- Gosto de ficção científica com política e filosofia.
- Procuro um livro curto e divertido.
- Meu dia foi uma droga.              (o bot acolhe e sugere leituras leves)
- Tô entediado, sem nada pra fazer.   (o bot sugere vira-páginas)
- Tô muito ansioso hoje.              (o bot sugere leituras calmas)
- Estou super animado!                (o bot sugere aventuras)
- Fale sobre Duna.
- Quero algo parecido com Harry Potter.
- mais opções                         (continua a recomendação anterior)
- mais curto                          (refina a recomendação anterior)
- Tchau.
