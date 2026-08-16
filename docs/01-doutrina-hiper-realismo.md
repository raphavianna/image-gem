# Doutrina de hiper-realismo

Etapa **E1**. Este é o documento de conteúdo do repositório: define o que torna uma imagem gerada indistinguível de uma fotografia e transforma isso em regras que a E2 codifica em schema, a E3 aplica por modalidade e a E4 instancia em templates.

Nada aqui é preferência estética. Cada eixo termina em **cláusula verificável** — a forma que a regra assume quando vira validação de campo. Quando uma afirmação técnica vem de fonte, ela carrega a etiqueta de origem de `docs/00-fontes/`: `[GAI]` documentação primeiro-parte, `[CB]` cookbook, `[BLOG]` guia do Google Cloud, `[SDK]` código do `google-genai`. O que não tem etiqueta é doutrina fotográfica deste repositório, e está identificado como tal na última seção.

---

## 1. Por que o adjetivo não funciona

O erro central do prompt ingênuo é pedir realismo como atributo. `photorealistic`, `hyper-realistic`, `8k`, `ultra detailed`, `award winning`, `masterpiece` são solicitações de **aparência de realismo**, e aparência de realismo é um estilo de renderização — aquele que a cultura visual associa a render 3D publicitário, a capa de artstation, a filtro de retoque. O modelo atende ao pedido: entrega a estética que esses termos designam no seu corpus de treino. O resultado é mais liso, mais simétrico, mais saturado e mais sintético.

O realismo não é um atributo da imagem. É uma **propriedade emergente da coerência causal** entre a cena e o aparato que a registrou. Uma fotografia real é o resultado determinístico de uma cadeia física:

```
luz emitida → superfície (absorve, espalha, reflete) → óptica (foca, aberra, vinheta)
            → sensor (integra, satura, ruído) → revelação (curva, cor, grão)
```

Cada elo impõe consequências sobre o seguinte. Uma octabox de 1,5 m a 1,4 m do rosto **produz** uma penumbra de 3 a 4 cm na linha do maxilar; não é escolha decorativa, é geometria. `f/4` em médio formato **produz** um plano focal em que o olho próximo está nítido e o distante não. ISO 50 **produz** um grão fino específico. Quando essas consequências estão todas declaradas e mutuamente consistentes, o observador não encontra o ponto onde a física quebra — e é o ponto de quebra, não a falta de detalhe, que denuncia a imagem gerada.

Isso reformula o problema. Não escrevemos prompts descrevendo uma imagem bonita. **Escrevemos a especificação técnica de uma captura que poderia ter acontecido.** A diferença prática: toda afirmação do prompt deve ser rastreável a uma decisão que um fotógrafo real teria tomado, e nenhuma afirmação pode contradizer outra.

### O template oficial e por que ele não basta

A documentação primeiro-parte oferece este template, literal `[GAI]`:

> A photorealistic [type of shot] of a [subject description] in a [setting description]. [Description of the light]. Shot from a [camera angle] with a [lens type].

O template está correto no que faz: obriga tipo de plano, sujeito, cenário, luz, ângulo e lente — muito acima do prompt de uma linha. Mas é insuficiente para o nosso critério de aceitação por três razões concretas:

1. **Abre com o termo proibido.** O item 6 do checklist reprova o próprio template oficial.
2. **Os slots de luz e óptica são texto livre.** `[Description of the light]` aceita "soft lighting", que não determina penumbra, catchlight nem razão de contraste. `[lens type]` aceita "portrait lens", que não determina compressão nem profundidade de campo.
3. **Não exige coerência entre slots.** Nada impede declarar uma lente macro e um plano geral, ou luz dura e sombra difusa.

A doutrina deste repositório é um **superconjunto estrito** do template oficial: mantém os seis slots e acrescenta a obrigação de que cada um seja preenchido com grandezas físicas, e de que as grandezas concordem entre si. A orientação `[GAI]` de *"be hyper-specific"* é exatamente isto levado ao limite — a documentação diz que mais detalhe dá mais controle; a doutrina define **qual** detalhe.

### O que substitui o adjetivo

| Em vez de | Escreva |
|---|---|
| `photorealistic`, `hyper-realistic` | A cadeia câmera → luz → superfície → sensor, com números |
| `8k`, `ultra detailed` | A escala de textura correta para o enquadramento (poro visível a meio corpo, trama de tecido a curta distância) e a resolução no parâmetro estruturado, não no texto |
| `sharp focus` | O plano focal explícito: o que está em foco crítico e o que cai fora |
| `studio lighting` | Tamanho, distância, azimute, elevação, modificador e temperatura de cada fonte |
| `beautiful`, `perfect` | Assimetria declarada e o orçamento de imperfeição |
| `award winning`, `masterpiece` | A intenção da captura: "a single working frame from a commercial session" |

A última linha tem apoio em fonte: `[GAI]` recomenda *"provide context and intent — explain the purpose of the image"*. Declarar que o quadro é um frame de trabalho de uma sessão comercial informa o modelo do regime de produção, e regime de produção carrega consigo o acidente que a perfeição sintética não tem.

---

## 2. Os oito eixos

### Eixo 1 — Câmera e óptica

**O que declarar.**

*Corpo e formato de sensor.* O formato determina a relação entre distância focal e ângulo de visão, e por consequência a perspectiva facial e a profundidade de campo. Médio formato (Phase One, Fujifilm GFX, Hasselblad) com uma focal longa dá compressão facial suave e profundidade de campo rasa a aberturas moderadas — a assinatura do retrato editorial. Full-frame 35mm é o padrão de reportagem e de moda em locação. APS-C aumenta a profundidade de campo para a mesma abertura nominal e enquadramento, o que importa quando se quer nitidez em profundidade sem fechar o diafragma.

*O trio de exposição como conjunto coerente.* Abertura, velocidade e ISO não são três adjetivos independentes: são um sistema em que cada valor tem consequência visível, e as três consequências precisam aparecer no prompt.

| Parâmetro | Consequência que precisa estar declarada |
|---|---|
| Abertura | Profundidade do plano focal, caráter e tamanho do bokeh, vinhetagem mecânica |
| Velocidade | Congelamento ou arrasto de movimento — inclusive movimento sutil, como uma mão ou um fio de cabelo |
| ISO | Grão de luminância e ruído de croma nas sombras |
| Formato de sensor | Compressão de perspectiva e profundidade de campo para a mesma focal |

Declarar `f/1.4` e depois descrever um cenário inteiro em foco é uma contradição que o modelo tenta resolver — e resolve mal, produzindo aquela nitidez uniforme que parece render.

*Geometria de captura.* Distância câmera-sujeito em metros e altura da câmera em relação à linha dos olhos. Isto é o que separa um retrato de um plano de vigilância: 2,1 m na altura dos olhos é a geometria do retrato corporativo; 0,8 m acima da linha dos olhos é a selfie; 1,2 m abaixo é o plano heroico. A distância também governa a perspectiva do rosto independentemente da focal — nariz aumentado é consequência de proximidade, não de lente grande-angular.

*Plano focal explícito.* Qual elemento está em foco crítico e o que cai fora, nomeadamente. Em retrato: o olho próximo em foco, o olho distante marginalmente fora, o ombro macio. Essa assimetria de foco entre os dois olhos é um dos sinais mais baratos e mais eficazes de captura real, porque é exatamente o que acontece com profundidade de campo rasa e é exatamente o que o modelo tende a não fazer sozinho.

*Caráter do bokeh.* Redondo no centro, com deformação em olho-de-gato progressiva em direção às bordas do quadro — consequência da vinhetagem óptica. Bokeh uniformemente circular em todo o quadro é assinatura de desfoque sintético.

*Imperfeições ópticas reais.* Aqui está uma das maiores diferenças entre imagem gerada e fotografia, e a mais fácil de corrigir:

- **Aberração cromática longitudinal**: franja fina magenta-verde em bordas de altíssimo contraste — o especular na borda do cabelo, o reflexo num chanfro polido. Sutil, sempre presente em lentes rápidas.
- **Vinhetagem mecânica**: um terço a um stop de queda nos cantos, dependente da abertura.
- **Distorção geométrica**: barril em focais curtas, almofada em teleobjetivas. Coerente com a focal declarada.
- **Veiling flare**: **apenas** quando há fonte de luz dentro do quadro ou no ângulo de incidência. Flare sem fonte que o justifique é um erro de física tão grave quanto sombra sem direção.

**Cláusula verificável.** Formato de sensor, focal, abertura, velocidade e ISO presentes e não nulos. Distância e altura da câmera presentes. Plano focal nomeia ao menos um elemento em foco crítico e um fora. Se `veiling_flare` está ativo, existe fonte de luz declarada no quadro ou em ângulo de incidência. Ver eixo 7 para a checagem ISO ↔ grão.

### Eixo 2 — Luz

Luz é o eixo de maior retorno por palavra investida. Uma cena com esquema de luz completo e todo o resto medíocre passa por fotografia; o inverso nunca.

**Cada fonte nomeada declara seis grandezas:** tamanho físico do modificador, distância ao sujeito, altura ou elevação, azimute, tipo de modificador e temperatura de cor. O tamanho e a distância juntos determinam o **tamanho angular** da fonte, e o tamanho angular é o que governa a dureza da sombra. Esta é a relação causal central do eixo:

> Fonte grande e próxima → sombra de borda larga e gradual. Fonte pequena e distante → sombra de borda estreita e definida.

Um softbox de 1,5 m a 1,4 m do rosto tem tamanho angular grande e produz uma penumbra de vários centímetros no maxilar. O sol, apesar de enorme, está a 150 milhões de km — tamanho angular de meio grau, sombra de borda quase dura. Declarar "luz suave do sol a pino" é fisicamente incoerente, a menos que se declare a nuvem que faz a difusão, e aí a nuvem é a fonte.

**Razão key:fill numericamente.** `3:1` é o retrato corporativo padrão — modelagem visível, sombra aberta. `8:1` é dramático, sombra fechada. `1.5:1` é beleza e moda de catálogo. Escrever "well lit" não determina nada; escrever `3:1` determina a densidade de cada sombra do rosto.

**Comportamento da sombra como consequência, não como decoração.** Três coisas separadas, que precisam estar todas presentes:

1. **Largura da penumbra**, proporcional ao tamanho angular da fonte, declarada em centímetros na região onde importa.
2. **Sombra de contato e oclusão ambiente** onde superfícies se tocam — a base do sapato no carpete, o objeto sobre a mesa, o queixo sobre o pescoço. Sua ausência é o que faz objetos parecerem flutuar e é um dos sinais de IA mais imediatos.
3. **Direção da sombra projetada**, única e consistente para todos os elementos da cena. Duas direções de sombra numa mesma cena são o defeito estrutural mais comum em composição multi-imagem.

**Catchlight como assinatura verificável.** O reflexo da fonte no olho tem a **forma do modificador**: octabox dá octógono de cantos macios, beauty dish dá círculo com núcleo, strip box dá retângulo alongado, janela dá quadrilátero com divisões. A posição do catchlight nos dois olhos é coerente com o azimute da fonte, e o catchlight do olho mais distante é menor e mais fraco. Isto é gratuito de declarar e é uma das provas mais rápidas de que a luz descrita e a luz renderizada são a mesma.

**Luz de fundo e separação.** Fundo iluminado separadamente, com sua própria exposição relativa em stops. Uma luz de recorte por trás define a silhueta contra o fundo — e em cabelo, cria o halo de fios soltos que carrega textura.

**Mistura de fontes.** Quando há práticas em cena (luminária, tela, janela), suas temperaturas divergem, e a divergência é assinatura de realidade. O caso canônico é exterior: sol a 3200K no fim da tarde enquanto o preenchimento vem da cúpula do céu a 12000K. A sombra do rosto puxa para o azul enquanto a luz de recorte permanece quente. Nenhum esquema de estúdio de fonte única reproduz isso, e é por isso que exterior sintético costuma parecer estúdio com fundo trocado.

**Cláusula verificável.** Toda fonte declara tamanho, distância, azimute, elevação e temperatura de cor. Razão key:fill numérica presente. Largura de penumbra declarada e coerente com tamanho angular da fonte principal. Direção de sombra projetada única e declarada. Se há pessoa no quadro, forma do catchlight declarada e correspondente ao modificador da key.

### Eixo 3 — Pele

Em cena com pessoa, a pele é onde a imagem gerada morre. O defeito não é falta de resolução — é **uniformidade**. O modelo tende a produzir uma superfície de textura homogênea, simétrica, com brilho difuso constante. Pele real não tem nenhuma dessas três propriedades.

**Poro na escala do enquadramento.** Poro visível não significa poro por toda parte: significa a escala correta para a distância de captura. Em plano de meio corpo o poro é textura de grão fino; em close o poro é estrutura individual com variação de tamanho por região. Declarar "true pore scale for this framing" amarra a textura ao enquadramento em vez de deixá-la solta.

**Pelo velus.** O pelo fino e claro do maxilar, do buço e do halo da linha do cabelo. Contra a luz de recorte, forma um halo luminoso finíssimo. É invisível na descrição e altamente visível no resultado — sua ausência produz aquela borda de rosto "recortada" que denuncia composição.

**Espalhamento subsuperficial.** A pele é translúcida. Onde o tecido é fino e há luz por trás — borda da orelha, asa do nariz, dedos contra a fonte —, a luz atravessa e emerge avermelhada. Ausência de SSS é o que faz a pele parecer plástico pintado.

**Especular de sebo com gradiente por região.** A zona T (dorso do nariz, centro da testa, arco do cupido) é **mensuravelmente mais reflexiva** que as maçãs do rosto. Declarar o gradiente, não só o brilho. Brilho uniforme no rosto inteiro é maquiagem de render, não pele.

**Assimetria declarada e específica.** Genérica não serve: "slightly asymmetric face" não determina nada. Específica determina: a sobrancelha esquerda marginalmente mais alta, o canto esquerdo da boca subindo um pouco mais. Rosto humano é assimétrico em eixos independentes, e a simetria perfeita é talvez o sinal de IA mais reconhecível em retrato.

**Marcas preservadas.** Pintas com posição e tamanho em milímetros, sardas contadas, cicatrizes com comprimento e local, rubor capilar no nariz, nas orelhas e nos nós dos dedos. Estas marcas cumprem dupla função: quebram a uniformidade **e** são o portador de identidade entre gerações (ver seção 5).

**Textura variando por região.** Testa, maçãs, ao redor dos olhos, lábios e pescoço têm texturas diferentes. Lábios com ressecamento fino e vincos verticais visíveis; pescoço com textura mais fina que a testa.

**Proibido explicitamente na cauda:** pele aerografada, cerosa, plástica, textura uniforme sem poro, "glow" de filtro, simetria facial perfeita, dentes fosforescentes.

**Cláusula verificável.** Se há pessoa no quadro: escala de poro, especular de zona T com gradiente, ao menos uma assimetria específica e ao menos uma marca preservada estão todos presentes e não genéricos.

### Eixo 4 — Anatomia e modos de falha conhecidos

Falhas anatômicas são categóricas: quando aparecem, a imagem é descartada, não corrigida. Elas se concentram em cinco lugares previsíveis.

**Mãos.** Cinco dedos, articulação correta, leito ungueal visível, rugas nos nós, proporção de falanges. Quando as mãos não são o assunto, a defesa mais eficaz é composicional: enquadrar fora, ocupá-las com um objeto de geometria clara, ou apoiá-las em superfície. Quando são o assunto, especificar contagem e articulação explicitamente e reforçar na cauda.

**Dentes.** Individuais, com variação de tom e alinhamento, sem fluorescência. A falha típica é uma fileira contínua e uniformemente branca. Expressão de boca fechada ou meio sorriso elimina a superfície de risco inteira — e é por isso que os exemplos âncora usam meio sorriso de boca fechada.

**Olhos.** Catchlight com a forma do modificador e posição coerente entre os dois. Anel límbico definido. Esclera com vascularização fina em vez de branco puro — esclera branca é sinal de IA imediato. Fibras de íris com estrutura radial. Direção de olhar naturalmente assimétrica: os dois olhos não convergem em paralelo perfeito.

**Cabelo.** Separação de mechas, fios soltos, halo de fios individuais contra a luz de recorte. A falha típica é a massa selada — cabelo como volume sólido esculpido. Fios soltos são também parte do orçamento de imperfeição.

**Orelhas.** Relevo interno — hélice, anti-hélice, trago, concha. A orelha é raramente o assunto e por isso é onde o modelo economiza; uma orelha lisa é um defeito silencioso mas percebido.

**Cláusula verificável.** Se há mãos visíveis, contagem e articulação declaradas e presentes na cauda. Se há boca aberta, dentes individuais declarados. Se há pessoa, catchlight e esclera declarados.

### Eixo 5 — Vestuário e materiais

Tecido é a segunda maior área do quadro em retrato, e responde por boa parte da sensação de peso e de realidade.

**Trama visível na escala do enquadramento.** Nomear o tecido e a trama: sarja de lã crepe, seda crua, algodão penteado, denim. A trama tem direção e periodicidade e aparece de forma diferente em cada distância.

**Vincos nos pontos de tensão.** Roupa real amassa onde o corpo dobra e onde o peso puxa: dobra interna do cotovelo, cintura, rolo onde a gola encontra o pescoço, tensão no ombro. Roupa sem vincos é roupa de manequim 3D.

**Costura e ponto.** Ponto visível, com passo regular mas não perfeito. Bainha, pesponto, entretela.

**Desgaste.** Bordas puídas, pilling de fibra em zonas de atrito, brilho de uso em cotovelos, escurecimento de couro nas dobras.

**Caimento sob gravidade compatível com o material declarado.** Lã crepe cai pesado com dobras largas; seda cai fluido com dobras estreitas e frequentes; denim resiste e forma vincos angulares. Declarar o tecido sem declarar o caimento correspondente deixa a decisão para o modelo, que tende ao caimento genérico.

**Cláusula verificável.** Tecido nomeado com trama. Ao menos um ponto de tensão com vinco declarado. Caimento coerente com o peso do tecido nomeado.

### Eixo 6 — Ambiente e integração

**Perspectiva e linha do horizonte consistentes** entre sujeito e cenário. Em composição, é o erro que mais denuncia: sujeito fotografado na altura dos olhos colado num fundo capturado de baixo.

**Geometria de reflexo correta.** Toda superfície especular reflete o que está geometricamente na posição de reflexão — e nada que não esteja declarado na cena. Um reflexo que implica uma fonte de luz não declarada é uma contradição.

**Perspectiva atmosférica.** Em profundidade, o contraste cai e a saturação diminui com a distância. Separa planos sem depender só de desfoque.

**Oclusão ambiente nos pontos de contato** entre sujeito e cenário — ver eixo 2.

**Em céu aberto**, declarar em vez de nomear a hora: elevação e azimute solares em graus, condição de céu (limpo, encoberto, nublado alto) e a consequência disso na dureza da sombra e na temperatura do preenchimento vindo do céu. "Golden hour" é rótulo; "sol a 8 graus de elevação e 250 graus de azimute" é geometria, e a geometria determina o comprimento e a direção da sombra projetada, a largura da penumbra crescendo com a distância do ponto de contato, e a divergência de temperatura entre luz principal e preenchimento.

**Cláusula verificável.** Se a cena é exterior: elevação e azimute solares em graus, condição de céu, e temperatura do preenchimento declaradas. Se há superfície especular: o que ela reflete está declarado. Ponto de contato entre sujeito e cenário tem sombra de contato declarada.

### Eixo 7 — Cor e revelação

**Perfil de referência real.** Uma emulsão nomeada (Kodak Portra 400, Fujifilm Pro 400H, Kodak Ektar 100, Ilford HP5) ou um perfil digital neutro declarado. A emulsão carrega consigo uma paleta inteira — saturação contida, meios-tons quentes, verdes puxados para o frio, no caso do Portra — em duas palavras.

**Rolloff gradual de altas luzes.** Sem estouro. O ponto onde a testa ou o chanfro polido satura em branco puro é onde a imagem revela compressão digital grosseira.

**Ponto de preto não esmagado.** A sombra mais profunda declarada em percentual de luminância — 5 a 8 por cento, não zero absoluto. Preto absoluto em cena com luz ambiente é fisicamente impossível e visualmente sintético.

**Grão proporcional ao ISO declarado.** Esta é a checagem de coerência mais direta do eixo 1: ISO 50 em médio formato dá grão de luminância finíssimo; ISO 3200 dá grão grosso e ruído de croma visível nas sombras. Declarar ISO 100 e "heavy film grain" é contradição.

**Evitar** teal-orange saturado e halos de HDR — as duas assinaturas de pós-processamento que gritam "imagem tratada".

**Cláusula verificável.** Perfil de cor nomeado. Rolloff de altas luzes e ponto de preto em percentual declarados. Descrição de grão coerente com o ISO do eixo 1.

### Eixo 8 — Orçamento de imperfeição

Uma fotografia real é um instante recortado de um processo contínuo e desordenado. Contém acidente. A imagem gerada, deixada por conta própria, converge para o instante ideal: pose resolvida, cabelo no lugar, expressão completa, superfície limpa. É o **vale da perfeição sintética** — a imagem não tem defeito nenhum e por isso não parece real.

A contramedida é prescrever **de uma a três imperfeições controladas e específicas**. Uma é pouco em cena complexa; mais de três começa a parecer encenação de desleixo.

Categorias que funcionam:

| Categoria | Exemplos |
|---|---|
| Acidente de estilo | Um fio de cabelo caído na testa, não penteado de volta; gola levantada de um lado pelo vento |
| Acidente de movimento | Arrasto leve numa mão; piscar parcial; expressão pega entre dois tempos |
| Acidente de fabricação | Uma costura milímetros fora do esquadro; um ponto mais apertado que os vizinhos |
| Acidente de ambiente | Uma partícula de poeira fora do foco crítico; uma marca de manuseio visível só na banda especular |
| Acidente de captura | Enquadramento com folga desigual; um elemento cortado pela borda |

**A regra decisiva é a especificidade.** "Some imperfections" não produz nada. "One strand of hair has fallen across the forehead and has not been styled back" produz exatamente aquilo. A imperfeição precisa ser tão especificada quanto a luz.

**Cláusula verificável.** Entre uma e três imperfeições, cada uma com localização e natureza específicas. Nenhuma formulada de forma genérica.

---

## 3. Cenas sem humanos — produto, still life, arquitetura

Os eixos 3 e 4 não se aplicam. A denúncia de IA muda de endereço, e a mudança é mais profunda do que "tirar a pele da lista": em cena com pessoa, o observador julga contra um modelo perceptual altamente treinado de rostos; em cena sem pessoa, ele julga contra o comportamento da luz nos materiais. **A carga de realismo migra da pele para a resposta especular.**

Cinco denúncias específicas, e a contramedida de cada uma:

**1. Resposta de material uniforme.** O defeito dominante. Todas as superfícies com o mesmo micro-brilho, como se o mundo inteiro fosse feito de um único material com cor trocada. A contramedida é o análogo direto do gradiente de zona T da pele: **cada superfície nomeada declara sua própria resposta especular** — o que reflete, o que espalha, com que geometria.

| Acabamento | Resposta a declarar |
|---|---|
| Polido / espelhado | Reflete com geometria legível: o reflexo tem forma e posição determinadas pela fonte |
| Escovado / acetinado | Espalha a fonte numa banda direcional, seguindo a direção do grão |
| Fosco / honed | Devolve um duplo difuso e escuro, sem imagem especular |
| Vidro com tratamento AR | Transmite com resíduo especular fraco e dominante de cor no ângulo rasante |
| Couro / têxtil | Espalhamento amplo com micro-especular no relevo do grão |

**2. Geometria de reflexo incorreta ou impossivelmente limpa.** Reflexos que não correspondem a nada declarado na cena, ou superfícies polidas devolvendo um ambiente perfeito e vazio. A regra de fechamento: **nada nos reflexos pode implicar uma fonte de luz que não esteja declarada.** É a cláusula que impede o modelo de inventar iluminação.

**3. Tipografia e texto de rótulo deformados.** Falha catastrófica em produto, porque o olho lê texto com tolerância zero. Contramedidas em três camadas: declarar a tipografia como correta e com kerning correto no bloco de materiais; proteger na cauda `AVOID` com `deformed dial typography` ou equivalente; e, para rótulos com texto substancial, aplicar a recomendação `[GAI]` — *"when generating text for an image, Gemini works best if you first generate the text and then ask for an image with the text"*, isto é, resolver o texto num turno anterior.

**4. Ausência de micro-defeitos de fabricação e de uso.** O eixo 8 continua valendo, mudando de categoria: um ponto de costura mais apertado que os vizinhos, um microrrisco de manuseio no fecho visível apenas na banda especular, uma partícula de poeira fora do foco crítico. Produto real saiu de uma fábrica e passou por mãos.

**5. Sombra de contato ausente ou flutuante.** O objeto parece pairar milímetros acima da superfície. A sombra de contato é densa e apertada no ponto de toque e abre em penumbra com a distância — e a taxa de abertura é consequência do tamanho angular da fonte, exatamente como no eixo 2.

**Regra de desempate para cenas mistas.** Quando há pessoa **e** produto no quadro — uma mão segurando o objeto, um modelo vestindo a peça —, os dois conjuntos se aplicam cumulativamente, não alternativamente. O item 4 do checklist de emissão exige então **ambos**: a especificação de pele para a região de pele visível, e a resposta especular para cada superfície nomeada do produto. Não há escolha entre eles; a regra é `há pele visível → especifique pele` e `há superfície nomeada → especifique sua resposta`, avaliadas independentemente.

---

## 4. Tabela diagnóstica — sinal de IA → contramedida

Esta tabela é a ferramenta de trabalho da E6: quando uma geração sai errada, localiza-se o sinal na coluna 1 e aplica-se a coluna 3. A coluna 4 é o endereço da correção no schema da E2 — é o que torna a tabela executável em vez de descritiva.

### 4.1 Cenas com pessoas

| Sinal de IA observado | Causa provável | Contramedida no prompt | Campo do schema |
|---|---|---|---|
| Pele lisa, cerosa, sem poro | Textura não especificada; termo de estilo puxou para render | Escala de poro para o enquadramento; textura variando por região; `AVOID` airbrushed/waxy | `skin.pore_scale`, `skin.regional_variation` |
| Brilho uniforme no rosto | Especular declarado sem gradiente | Zona T mensuravelmente mais reflexiva que as maçãs | `skin.specular_zones` |
| Rosto simétrico demais | Assimetria ausente ou genérica | Duas assimetrias específicas em eixos independentes | `subject.asymmetry[]` |
| Rosto "recortado" contra o fundo | Ausência de pelo velus e de luz de recorte | Velus no maxilar e no halo do cabelo; rim light declarada | `skin.vellus`, `lighting.rim` |
| Pele parece plástico pintado | Ausência de espalhamento subsuperficial | SSS em bordas de orelha, asa do nariz, dedos contra a luz | `skin.subsurface` |
| Olhos "mortos" ou vidrados | Catchlight ausente ou genérico | Catchlight com forma do modificador, posição por azimute, menor no olho distante | `lighting.catchlight_shape` |
| Esclera branco puro | Não especificada | Vascularização fina na esclera; anel límbico | `anatomy.eyes` |
| Dentes uniformes e fosforescentes | Boca aberta sem especificação | Dentes individuais com variação; ou expressão de boca fechada | `anatomy.teeth`, `subject.expression` |
| Cabelo como massa sólida | Não especificado | Separação de mechas, fios soltos, halo contra a rim light | `anatomy.hair` |
| Mãos malformadas | Mãos visíveis sem especificação | Cinco dedos, articulação, leito ungueal; ou enquadrar fora; reforço na cauda | `anatomy.hands`, `frame.crop` |
| Ambos os olhos igualmente nítidos com bokeh forte | Plano focal não declarado | Olho próximo em foco crítico, olho distante marginalmente fora | `camera.focal_plane` |
| Bokeh circular uniforme até as bordas | Caráter de bokeh não declarado | Deformação em olho-de-gato progressiva nas bordas | `optics.bokeh_character` |
| Cena inteira nítida apesar de abertura grande | Contradição abertura ↔ profundidade | Reconciliar: ou fechar a abertura, ou declarar a queda de foco | coerência `aperture` ↔ `focal_plane` |
| Imagem "limpa demais", sem grão | ISO declarado sem consequência | Grão de luminância proporcional ao ISO; croma sutil nas sombras | coerência `iso` ↔ `render.grain` |
| Sombra sem direção clara ou com duas direções | Direção não declarada, ou composição | Direção única declarada e aplicada a todos os elementos | `lighting.shadow_direction` |
| Sombra com dureza incompatível com a fonte | Tamanho angular não declarado | Tamanho e distância da fonte; penumbra em cm | `lighting.sources[].size/distance` |
| Sujeito parece flutuar sobre o chão | Sombra de contato ausente | Sombra de contato densa no toque, abrindo em penumbra | `environment.contact_shadow` |
| Roupa de manequim, sem peso | Vincos e caimento não declarados | Vincos nos pontos de tensão; caimento coerente com o tecido | `wardrobe.creases`, `wardrobe.drape` |
| Cor teal-orange, halos de HDR | Perfil de cor não declarado | Emulsão nomeada; rolloff gradual; preto em 5–8% | `render.color_profile` |
| Imagem perfeita e sem vida | Orçamento de imperfeição vazio | 1 a 3 imperfeições específicas e localizadas | `imperfection_budget[]` |
| Exterior parece estúdio com fundo trocado | Preenchimento sem divergência de temperatura | Sol quente + cúpula de céu fria, com a diferença declarada em stops e K | `lighting.sky_fill` |
| Flare sem fonte visível | Flare decorativo | Remover, ou declarar a fonte no quadro que o justifica | coerência `flare` ↔ `lighting.in_frame` |

### 4.2 Cenas sem humanos — produto, still life, arquitetura

| Sinal de IA observado | Causa provável | Contramedida no prompt | Campo do schema |
|---|---|---|---|
| Todas as superfícies com o mesmo micro-brilho | Resposta especular não declarada por superfície | Cada superfície nomeada declara reflete/espalha e com que geometria | `materials[].specular_response` |
| Reflexo implica luz não declarada | Geometria de reflexo livre | Cláusula de fechamento: nada nos reflexos implica fonte não declarada | `materials[].reflection_geometry` |
| Superfície polida devolve ambiente vazio e perfeito | Conteúdo do reflexo não declarado | Declarar o que cada superfície polida reflete | `materials[].reflects` |
| Simetria especular perfeita | Reflexo tratado como espelho ideal | Atenuação e contraste reduzido no reflexo; `AVOID` mirror-perfect symmetry | `materials[].reflection_falloff` |
| Tipografia de rótulo deformada | Texto não protegido | Tipografia correta com kerning no bloco de materiais; proteção na cauda; texto resolvido em turno anterior | `materials[].typography` |
| Objeto flutuando | Sombra de contato ausente | Sombra densa no toque abrindo em penumbra | `environment.contact_shadow` |
| Produto novo demais, de catálogo 3D | Micro-defeitos ausentes | Defeito de fabricação e marca de manuseio específicos | `imperfection_budget[]` |
| Hotspot estourado em superfície curva | Fonte não modelada, sem feathering | Softbox strip com feathering; banda contínua em vez de ponto | `lighting.sources[].feathering` |
| Nitidez uniforme em toda a profundidade | Focus stacking implícito | Declarar quadro único com queda de foco honesta | `camera.focal_plane`, `camera.stacking: false` |
| Bordas com halo de supernitidez | Não declarado | `AVOID` oversharpened edges; rolloff gradual | `render.highlight_rolloff` |
| Arquitetura com linhas convergentes erradas | Perspectiva não declarada | Linha do horizonte e altura de câmera; correção de basculamento se aplicável | `camera.height`, `environment.horizon` |

### 4.3 Modos de falha exclusivos de edição e composição

| Sinal de IA observado | Causa provável | Contramedida no prompt | Campo do schema |
|---|---|---|---|
| Sujeito sutilmente alterado numa troca de fundo | Bloco de preservação ausente ou vago | `PRESERVE` explícito e exaustivo **antes** da alteração | `edit.preserve[]` |
| Borda de recorte ou halo no cabelo | Integração não declarada | Proibir cut-out edges na cauda; declarar integração de borda | `edit.avoid[]` |
| Duas direções de luz no rosto | Nova cena não reconciliada com a luz já gravada | Bloco `RECONCILE LIGHT`: o novo ambiente justifica a luz existente | `edit.light_reconciliation` |
| Segundo catchlight aparece | Nova fonte introduzida sem controle | Proibir explicitamente catchlight adicional ou deslocamento do existente | `edit.preserve.catchlight` |
| Paleta do fundo novo destoa do sujeito | Grading não casado | Casar paleta e rolloff do fundo com o quadro de origem | `edit.color_match` |
| Identidade deriva ao longo de vários turnos | Referência não realimentada | Realimentar a geração anterior como referência do turno seguinte `[GAI]` | `character.reference_chain` |

---

## 5. Consistência de personagem — regra derivada das fontes

Capability declarada como **primeira** da lista do modelo `[CB]`, e o ponto que o prompt-mestre marcou como de menor cobertura. Esta seção deriva a regra prática das fontes; os templates da E4 que usam referência a herdam.

### 5.1 O que as fontes estabelecem

**Não existe campo de identidade na API.** O `[SDK]` só expõe `SubjectReferenceConfig` e afins no caminho Imagen/Vertex, não em `ImageConfig`. A referência entra como **elemento da lista de entrada, ao lado do texto** `[CB]`. Consequência direta e não negociável: **a separação entre o que é invariante e o que varia é feita no texto do prompt.** Não há parâmetro para isso. É por isso que a gramática de preservação existe.

**Orçamentos de referência por papel** — tabela literal `[GAI]`, para `gemini-3-pro-image`:

| Papel da referência | Teto |
|---|---|
| Personagens para consistência de identidade | **5** |
| Objetos em alta fidelidade | 6 |
| Referências de estilo | 3 |
| **Total por requisição** | **14** |

Os três orçamentos somam o teto: 6 + 5 + 3 = 14. O "14" nunca foi um teto indiferenciado.

> **Correção de decisão travada, aprovada em 2026-08-16.** O ESTADO fixava "teto de 6 imagens para qualquer template que dependa de identidade preservada", derivado de `[CB]`. A documentação primeiro-parte — autoridade para limites pela hierarquia do prompt-mestre — mostra que **6 é o orçamento de objetos e 5 é o de personagens**. A regra deste repositório é **5 referências de identidade**; 6 permanece válido como teto de objetos em alta fidelidade. Ver `docs/00-fontes/05-divergencias-e-lacunas.md`, D2.

**A ordem de declaração importa.** Literal `[BLOG]`:

> State what must stay identical before you state what changes. This is important because most bad edits come from the model rebuilding something you never asked it to touch.

O modo de falha nomeado pela própria fonte é o modelo **reconstruir** o que ninguém pediu para tocar. Preservação primeiro não é estilo, é contramedida.

**O template oficial de preservação**, literal `[GAI]`:

> Using the provided images, place [element from image 2] onto [element from image 1]. Ensure that the features of [element from image 1] remain completely unchanged.

**O padrão de encadeamento**, literal `[GAI]`:

> For best results, include previously generated images in subsequent prompts to maintain consistency. For complex poses, include a reference image of the selected pose.

**O que carrega identidade, segundo a fonte.** O que o autor do `[CB]` aponta como prova de consistência entre gerações são **traços idiossincráticos** — o nariz peculiar, os olhos de cores diferentes —, não a média do rosto. Isso converge exatamente com o eixo 3: são as marcas específicas, não a geometria genérica, que sobrevivem à regeneração.

### 5.2 A regra prática

**Duas classes, declaradas separadamente e sempre nesta ordem.**

**Classe invariante — sempre declarada explicitamente, sempre primeiro:**

- Geometria facial: proporções, formato do maxilar, distância interocular, formato do nariz e da boca.
- Marcas: cada pinta, sarda, cicatriz, com posição e tamanho. **Este é o portador primário de identidade** — é o que a fonte identifica como prova de consistência, e é o mais barato de declarar textualmente.
- Assimetrias específicas, as mesmas em toda a série.
- Tom e textura de pele.
- Estrutura de cabelo, quando a identidade depende dela.

**Classe variável — só varia o que foi explicitamente autorizado a variar:**

- Pose, ângulo de câmera, expressão.
- Esquema de luz e ambiente.
- Vestuário, quando não faz parte da identidade.
- Enquadramento e proporção.

**Cinco regras operacionais.**

1. **Ordem fixa:** invariante antes de variável, sempre. Fonte: `[BLOG]`, citação acima.
2. **Teto de 5 referências de identidade** por requisição. Acima disso, o orçamento declarado é excedido e a fidelidade cai. Para exceder o total de 14, o contorno oficial `[CB]` é combinar imagens numa colagem antes de enviar.
3. **Encadeamento:** em série de mais de uma geração, realimentar a saída aprovada do turno anterior como referência do turno seguinte `[GAI]`. Não regenerar cada quadro a partir da referência original — a deriva se acumula.
4. **Chat, não chamadas unárias.** Modelos Gemini 3 carregam *thought signatures* que preservam o raciocínio anterior, não só o texto `[CB]`. O refinamento iterativo em `client.chats` mantém mais estado que uma sequência de chamadas independentes.
5. **A cauda `AVOID` de uma geração com identidade preservada é diferente da cauda de geração livre:** ela precisa proibir explicitamente alteração de traço facial, deriva de tom de pele, e remoção das marcas declaradas.

**Cláusula verificável.** Em template com identidade preservada: bloco de invariantes presente e anterior ao bloco de variáveis; ao menos duas marcas específicas declaradas; número de referências de identidade ≤ 5; cauda contendo proibição de alteração facial.

---

## 6. Checklist de emissão — forma final

Este é o proxy verificável do critério de aceitação, e o contrato entre a E1 e a E2. **Binário: nenhum prompt sai do sistema com qualquer item reprovado.** A E2 codifica cada item como validação sobre o schema; cada renderizador de modalidade da E3 o executa antes de emitir.

| # | Item | Condição de aprovação | Aplicabilidade |
|---|---|---|---|
| **1** | **Fontes de luz completas** | Toda fonte declara tamanho físico, distância, azimute, elevação e temperatura de cor | Sempre |
| **2** | **Trio de exposição coerente** | Grão corresponde ao ISO; plano focal e bokeh correspondem à abertura e ao formato de sensor; congelamento ou arrasto corresponde à velocidade | Sempre |
| **3** | **Direção de sombra única** | Uma só direção de sombra projetada, declarada e válida para todos os elementos | Sempre |
| **4a** | **Pele** | Se há pessoa: escala de poro, especular de zona T com gradiente, ao menos uma assimetria específica e ao menos uma marca preservada | Se há pessoa |
| **4b** | **Materiais** | Se há superfície nomeada: sua resposta especular declarada — o que reflete, o que espalha, com que geometria | Se há superfície nomeada |
| **5** | **Orçamento de imperfeição** | De 1 a 3 imperfeições, cada uma específica e localizada. Nenhuma genérica | Sempre |
| **6** | **Termos proibidos** | Zero ocorrências de `photorealistic`, `hyper-realistic`, `8k`, `ultra detailed`, `award winning`, `masterpiece` | Sempre |
| **7** | **Cauda de restrições** | Existe, é curta, é delimitada, e contém **apenas** modos de falha relevantes ao cenário | Sempre |
| **8** | **Orçamento de densidade** | Comprimento dentro da faixa da modalidade (350–500 palavras no corpo) | Sempre |

**Notas de aplicação.**

**Item 4 não é excludente.** `4a` e `4b` são avaliados independentemente. Cena com pessoa e produto passa pelos dois; cena de produto puro passa só por `4b`; retrato em fundo liso passa por `4a` e por `4b` apenas se alguma superfície do cenário estiver nomeada.

**Item 6 é literal e case-insensitive.** A busca é por string. A lista é fechada e não deve ser expandida por julgamento — termos ruins que não estejam nela são problema de qualidade, não de reprovação automática.

**Item 7 tem critério de admissão.** A cauda existe para **modos de falha de renderização**, não para conteúdo de cena. `airbrushed skin`, `malformed hands`, `CGI look`, `deformed typography` são admissíveis: não têm formulação positiva equivalente. `no cars`, `no people in the background` **não** são admissíveis — conteúdo de cena se declara positivamente, conforme `[GAI]`: *"instead of saying 'no cars,' describe the intended scene positively."* Esta é a reconciliação entre a orientação oficial de prompts negativos semânticos e a cauda `AVOID` adotada pelo repositório: elas não conflitam porque tratam de coisas diferentes.

**Item 8 conta o corpo.** Nas modalidades 3 e 4, proporção e resolução saem do texto e vão para os parâmetros estruturados; o corpo permanece na mesma faixa. O renderizador reporta a contagem, conforme o orçamento de densidade do prompt-mestre.

**Ordem de sacrifício quando o item 8 reprova por excesso**, do prompt-mestre e repetida aqui porque é operacional: cortar primeiro detalhes secundários de ambiente, depois vestuário, depois óptica fina (aberrações). **Nunca cortar:** esquema de luz, pele ou materiais, orçamento de imperfeição — porque são exatamente os itens 1, 4 e 5, e cortá-los reprova o prompt em outro item.

---

## 7. Rastreio — o que é fonte e o que é doutrina

Separação explícita, para que a E2 saiba o que pode ser questionado por evidência e o que é decisão de projeto.

**Derivado de fonte, com etiqueta:**

- Orçamentos de referência por papel — 5 personagens, 6 objetos, 3 estilo, 14 total `[GAI]`.
- Preservação declarada antes da alteração `[BLOG]`, `[GAI]`.
- Encadeamento de referência entre turnos `[GAI]`, `[CB]`.
- Prompts negativos semânticos para conteúdo de cena `[GAI]`.
- Especificidade como alavanca de controle `[GAI]`.
- Contexto e intenção influenciam a saída `[GAI]`.
- Texto resolvido antes da imagem que o contém `[GAI]`.
- Marcas idiossincráticas como portador de identidade `[CB]`.
- Ausência de campo de identidade na Gemini API `[SDK]`.

**Doutrina fotográfica deste repositório, sem etiqueta de fonte:** os oito eixos e seu conteúdo técnico, a tabela diagnóstica, a lista de termos proibidos, o orçamento de imperfeição, o critério de admissão à cauda `AVOID`, a regra de desempate para cenas mistas e a estrutura do checklist de emissão. Sustentam-se em fotografia e ciência da imagem, não em documentação de modelo. São falsificáveis empiricamente pelo loop da E6: se um registro em `runs/` mostrar que uma regra não melhora o resultado, a regra muda.

**Marcado `[NÃO VERIFICADO]` e relevante para esta doutrina:** o default e o comportamento exato de `person_generation` (L3), que condiciona a política de conteúdo mas não altera nenhum eixo. Nenhuma afirmação desta página depende dele.
