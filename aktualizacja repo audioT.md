Aktualizacja repozytorium audioT – integracja n8n i usługi transkrypcji

Opis: Poniżej przedstawiono dogłębną analizę dotychczasowych ustaleń z naszej rozmowy oraz wynikające z nich zmiany, które należy wprowadzić do repozytorium audioT (projekt transcriptoonAI). Celem jest uzyskanie kompletnego repozytorium stanowiącego podstawę do dalszych prac nad automatycznym transkrybowaniem audio za pomocą n8n oraz lokalnej usługi transkrypcji opartej o Whisper. Uwzględniono wszystkie istotne szczegóły naszej dyskusji – od struktury kafelków (węzłów) n8n i formatu plików workflow (.json) po specyfikację API transkrypcji, zadania do realizacji oraz wskazówki dotyczące projektowania promptów dla AI.

Przegląd projektu i dotychczasowych ustaleń

Cel projektu: Zautomatyzowanie procesu transkrypcji plików audio (np. z załączników e-mail) i generowanie raportów w Google Docs. Rozwiązanie ma działać w środowisku low-code przy użyciu platformy n8n (workflow automation), wspieranej przez własną usługę transkrypcji (kontener Docker z lokalnym modelem Whisper).

Główne komponenty:

Workflow n8n – przepływ automatyzacji, który monitoruje przychodzące e-maile z audio, pobiera pliki, wysyła je do usługi transkrypcji, a po otrzymaniu wyniku tworzy sformatowany dokument Google z transkrypcją.

Usługa transkrypcji (Whisper) – aplikacja FastAPI uruchomiona w kontenerze Docker, udostępniająca endpoint do transkrypcji audio przy użyciu modelu Whisper (biblioteka faster-whisper【39†】). Ma ona obsługiwać żądania transkrypcji, także w trybie asynchronicznym dla dłuższych plików.

Integracje z Google – wykorzystanie Gmail API (OAuth2) do monitorowania skrzynki pocztowej oraz Google Docs API do tworzenia/aktualizacji dokumentów z wynikami transkrypcji.

Ewentualne moduły AI – np. wykorzystanie modeli językowych (poprzez n8n Nodes for LangChain) do analizy transkrypcji: generowanie streszczeń, wyodrębnianie informacji, itp.

Szablon wyjściowy: Nasza dyskusja odnosiła się m.in. do przykładowego workflow “AI Audio Transcription & Google Docs Report Generator with VLM Run” dostępnego w społeczności n8n
n8n.io
. Wykorzystaliśmy go jako punkt odniesienia. Workflow ten wykonywał:

Monitorowanie Gmaila pod kątem załączników audio.

Przetwarzanie i transkrypcję audio przez zewnętrzną usługę VLM Run (AI transkrypcja) – z obsługą segmentacji tekstu i znaczników czasu.

Asynchroniczne otrzymanie wyniku (poprzez webhook) – co pozwala uniknąć timeoutów przy dłuższych nagraniach
n8n.io
.

Generowanie profesjonalnie sformatowanego raportu w Google Docs z uzyskaną transkrypcją (z podziałem na segmenty wraz z czasami).

Nasze modyfikacje: Zdecydowaliśmy się na zastąpienie usługi VLM Run własnym lokalnym serwisem transkrypcyjnym opartym o Whisper. Wymaga to następujących zmian:

Zaprojektowanie API transkrypcji kompatybilnego z potrzebami workflow (przyjmowanie pliku audio i zwracanie wyniku w zbliżonym formacie do VLM Run, w tym segmenty tekstu i znaczniki czasu).

Dostosowanie workflow n8n – w szczególności zamiana dedykowanego kafelka VLM Run na np. zapytanie HTTP do lokalnego API. Konieczne jest uwzględnienie parametru callback (URL webhooka n8n) przekazywanego do usługi, by zachować asynchroniczność przetwarzania dłuższych plików.

Uzupełnienie repozytorium o dokumentację i pliki konfiguracyjne: specyfikację API, opis działania workflow, listę zadań implementacyjnych oraz ewentualne wskazówki do projektowania promptów dla AI (np. jeśli dodamy moduły typu Information Extractor do analizy transkryptu).

Poniżej omówione są poszczególne obszary i pliki repozytorium, które należy zaktualizować, wraz z proponowaną zawartością. Wszystkie pliki utworzone lub uzupełnione zostały opisane zgodnie z ustaleniami – staramy się nie pominąć żadnego szczegółu z rozmowy.

Struktura kafelków n8n i format plików workflow (.json)

Jednym z kluczowych tematów rozmowy była budowa kafelków w n8n, czyli struktura danych opisująca węzły (nodes) oraz ich połączenia w wyeksportowanym pliku workflow (.json). Zrozumienie tej struktury jest ważne, aby móc ręcznie edytować lub generować workflow w plikach .json do importu w n8n. Poniżej podsumowanie zasad i elementów formatu:

Ogólna struktura pliku workflow: Plik .json eksportowany z n8n zawiera zwykle główne sekcje:

"name" – nazwa workflow.

"nodes" – lista obiektów, z których każdy opisuje pojedynczy kafelek/węzeł w workflow.

"connections" – obiekt definiujący połączenia między węzłami (który node przekazuje dane do którego).

Dodatkowe meta-informacje jak "active" (czy workflow jest aktywny), "settings", "tags", itp., które są generowane przez n8n.

Struktura obiektu pojedynczego węzła: Każdy element w tablicy "nodes" zawiera kluczowe pola definiujące kafelek:

name – czytelna nazwa węzła widoczna w edytorze n8n (np. "Download file" lub "Transcribe Audio" itp.).

type – identyfikator typu węzła, zwykle w formacie <pakiet>.<nazwaWęzła>. Przykłady:

Wbudowane nody n8n mają prefix "n8n-nodes-base" (np. "n8n-nodes-base.gmailTrigger" dla triggera Gmaila, "n8n-nodes-base.googleDrive" dla noda Google Drive).

Niestandardowe/community nodes mają prefixy wg swoich pakietów, np. "@vlm-run/n8n-nodes-vlmrun.vlmRun" dla kafelka VLM Run (custom node) czy "@n8n/n8n-nodes-langchain.googleGemini" dla użytego wcześniej noda LangChain (Google Gemini).

typeVersion – wersja noda (liczba zmieniająca się, gdy twórcy nodu aktualizują jego funkcjonalność). Musi być zgodna z wersją zainstalowanego nodu w n8n, inaczej mogą wystąpić błędy importu. Np. Gmail Trigger miał wersję 1.3, Google Drive 3 itd.【23†】.

position – współrzędne X, Y położenia kafelka na kanwie edytora (np. "position": [752, 1136]); nie wpływa na logikę, tylko na wygląd.

parameters – obiekt zawierający konfigurację konkretnego węzła, zależną od jego typu. To tutaj znajdują się ustawienia, które normalnie w interfejsie wprowadzamy w formularzu nodu. Przykłady:

Dla Gmail Trigger w parameters definiujemy np. kryteria wyszukiwania wiadomości, etykiety itp. (jeśli wymagane).

Dla nodu HTTP Request byłyby to URL, metoda, payload, itp.

Dla Google Drive – Download file w parameters widzimy np. operation: "download" i fileId (który może korzystać ze specjalnej struktury wyboru __rl – więcej poniżej).

Dla kafelka VLM Run lub innego API – parametry obejmowałyby m.in. wybór modelu, tryb (tu np. "inputType": "binary" dla Gemini, modelId itp.).

Dla Webhook – ustawia się np. unikalną ścieżkę (endpoint) webhooka, czy ma oczekiwać JSON, binaria itd.

Dla Google Docs – parametry obejmują m.in. documentURL (link/ID docelowego dokumentu Google) oraz akcje (np. wstawienie tekstu). W naszym przykładzie Google Docs node miał operation: "update" oraz zdefiniowane actionsUi z poleceniem wstawienia tekstu (transkrypcji)【37†】.

credentials – (opcjonalne) obiekt zawierający referencje do poświadczeń wymaganych przez węzeł. Jeśli dany kafelek korzysta z jakiegoś API wymagającego uwierzytelnienia, po dodaniu credentials w edytorze n8n eksport zawiera tu identyfikator powiązanych danych. Uwaga: Te identyfikatory (id) są specyficzne dla instancji n8n – importując workflow na innym serwerze, i tak trzeba w UI przypisać własne credentials. Dlatego przy ręcznym tworzeniu .json można ten fragment pominąć lub zostawić pusty, a po imporcie ustawić właściwe dane w GUI.

Przykład: w nodzie Google Drive w naszym wcześniejszym workflow pojawiło się:

"credentials": {
   "googleDriveOAuth2Api": {
      "id": "qSer271FT0..."
   }
}


co oznacza, że node oczekiwał użycia poświadczeń typu Google Drive OAuth2 (w n8n każdy credential ma nazwę typu, np. "googleDriveOAuth2Api") o identyfikatorze qSer... przypisanym w danej instancji n8n.

Połączenia między nodami: Sekcja "connections" definiuje, jak dane przepływają z jednego kafelka do drugiego. Struktura jest następująca:

Klucze obiektu "connections" to nazwy węzłów źródłowych (dokładnie takie, jak w ich polu name). Pod każdym kluczem mamy zazwyczaj obiekt zawierający przynajmniej klucz "main". Przykład:

"connections": {
  "Node A": {
    "main": [
      [
        { "node": "Node B", "type": "main", "index": 0 }
      ]
    ]
  }
}


Tutaj węzeł "Node A" przekazuje dane swoim głównym wyjściem ("main") do węzła "Node B" (gdzie index: 0 oznacza pierwszy port wejściowy B, zazwyczaj główny input). Struktura jest zagnieżdżona, ponieważ main jest tablicą (dla ewentualnych wielu wyjść nodu, np. niektóre kafelki mogą mieć więcej niż jedno wyjście), a wewnątrz jest lista połączeń (gdyby Node A łączył się do wielu następników). W powyższym przykładzie jest jedno połączenie z Node A do Node B.

Trigger/Start nodes: Węzły typu trigger (np. Gmail Trigger, Webhook w trybie słuchania) inicjują wykonanie workflow i zazwyczaj są pierwsze w swoim łańcuchu. W pliku JSON triggers również są łączone z następnymi nodami poprzez "connections". Np. Gmail Trigger może być źródłem dla kolejnego kroku. Ważne: W jednym workflow n8n może mieć wiele niezależnych ścieżek z różnymi triggerami. W naszym przypadku mamy dwa punkty startowe:

Gmail Trigger (nasłuch poczty) – rozpoczyna ścieżkę przekazującą plik audio do transkrypcji.

Webhook “Receive Transcription Results” – jest innym punktem startowym, uruchamianym przez zewnętrzne wywołanie (callback z serwisu transkrypcji) i prowadzi do utworzenia dokumentu w Google Docs.
W JSON każdy z tych triggerów będzie osobno wymieniony w connections tylko jeśli coś z niego wychodzi. W naszym eksporcie np. Webhook był połączony z Google Doc:

"Receive Transcription Results": {
  "main": [
    [ { "node": "Generate Transcription Report", "type": "main", "index": 0 } ]
  ]
}


co oznacza, że gdy tylko nadejdzie dane do webhooka, uruchomi on Generate Transcription Report (Google Docs)【24†】.
Natomiast brakowało (w naszym wyjściowym pliku) jawnego wpisu o połączeniu Gmail Trigger -> Transcription, co sugeruje, iż należy upewnić się, że taki związek zostanie dodany. Prawdopodobnie w trakcie konfiguracji trzeba ręcznie połączyć te kafelki (być może podczas eksportu coś się pominęło). Zasada jest taka: każde logiczne połączenie w edytorze n8n powinno mieć odzwierciedlenie w strukturze "connections".

Identyfikatory vs nazwy: n8n wykorzystuje nazwy węzłów jako klucze w connections. Dlatego ważne jest, by nazwy kafelków były unikalne (co edytor wymusza). Wewnątrz definicji połączenia stosuje się "node": "Nazwa Docelowego" aby wskazać, dokąd idą dane.

Uwagi dot. edycji ręcznej: Przy ręcznym pisaniu pliku JSON należy:

Dbać o poprawny format (łatwo o błąd składni, który uniemożliwi import). Warto użyć np. walidatora JSON.

Zapewnić zgodność nazw nodów i typów z faktycznie zainstalowanymi w n8n. Jeśli używamy niestandardowego kafelka, upewnijmy się, że pakiet jest zainstalowany (np. wspomniany node VLM Run wymagał zainstalowania pakietu n8n-nodes-vlmrun
n8n.io
 – w naszym przypadku z niego rezygnujemy na rzecz HTTP Request).

Pola typu id (identyfikatory kafelków) – w eksporcie n8n często są to unikalne UUID generowane przy tworzeniu nodu (np. "id": "36756cd7-19f6-4e66-af18-559f30a25f06" dla Download file). Nie są one stricte używane do referencji między nodami, więc ich unikalność nie jest krytyczna poza czytelnością i ewentualnym wykorzystaniem w logach. Przy tworzeniu nowego .json można użyć własnych UUID lub pozostawić puste – n8n może nadpisać je własnymi przy imporcie. Zaleca się jednak ustawienie losowych UUID, aby plik wygląda kompletnie.

W polu parameters mogą pojawić się wewnętrzne struktury jak __rl czy cachedResultName – np. w naszym pliku widzieliśmy:

"fileId": {
  "__rl": true,
  "mode": "list",
  "value": "<ID pliku>",
  "cachedResultName": "<ID pliku>"
}


Takie zapisy pojawiają się, gdy w interfejsie użytkownik wybiera np. plik z listy (n8n zachowuje ostatnio wybrany ID). Nie trzeba tego ręcznie modyfikować – można wpisać bezpośrednio fileId: "<ID>" lub zostawić strukturę. Istotne jest jednak poprawne podanie samego identyfikatora czy ścieżki potrzebnej do działania nodu.

Import do n8n: gotowy plik JSON importujemy poprzez interfejs n8n (np. funkcja Import from file). N8n zweryfikuje strukturę – w razie problemów wskaże linię błędu. Po imporcie warto przetestować workflow oraz ustawić brakujące elementy (zwłaszcza credentials dla usług Google, bo one z definicji nie przeniosą się automatycznie).

Podsumowując, pliki .json workflow muszą być starannie zbudowane. Nasza rozmowa podkreślała, że czasem łatwiej jest skonfigurować kafelki w UI i eksportować, ale znajomość formatu pozwala też na zaawansowane modyfikacje (np. globalne znaj/zamień jakiejś wartości, dodanie podobnego nodu przez skopiowanie fragmentu JSON itp.).

Specyfikacja API lokalnej usługi transkrypcji (transcription_api_spec.md)

Repozytorium zawiera katalog docker/whisper_local z prostym szkieletem aplikacji FastAPI (na razie tylko endpoint zdrowotny)
GitHub
. Musimy rozbudować tę usługę zgodnie z naszym planem. Poniżej proponowana specyfikacja API transkrypcyjnego – będzie ona zapisana w pliku cursor/CONTEXT/transcription_api_spec.md w repozytorium.

Endpoints API:

GET /health – Health check dla kontenera (już zaimplementowany jako zwracający {"status": "ok"}
GitHub
). Używany do sprawdzania, czy usługa działa (np. skrypt health_check.ps1 wysyła zapytanie na ten endpoint
GitHub
).

POST /transcribe – Główny endpoint do zlecania transkrypcji pliku audio.

Żądanie (Request): multipart/form-data lub inne odpowiednie – zawierające:

Plik audio do transkrypcji (np. pole file typu FileUpload). Wspierane formaty: MP3, WAV, M4A, AAC, OGG, FLAC itp. (Whisper obsługuje większość popularnych formatów audio – w tym skompresowane).

Opcjonalny parametr callback: np. pole formularza callbackUrl lub parametr zapytania ?callback=<URL>. Jest to URL webhooka n8n, pod który serwis wyśle wynik po zakończeniu transkrypcji (asynchronicznie). Jeśli zostanie podany ten URL, serwis może szybko odpowiedzieć (202 Accepted) i wykonać ciężką pracę w tle, aby nie blokować workflow n8n.

(Opcjonalnie można przewidzieć inne parametry, np. wybór modelu lub języka, ale na obecnym etapie nie jest to konieczne – domyślnie użyjemy modelu Whisper base albo innego, zgodnie z konfiguracją faster-whisper).

Odpowiedź (Response): Dwa scenariusze:

Tryb asynchroniczny (z callback): Serwis natychmiast zwraca potwierdzenie, np.

{"status": "processing", "jobId": "<opcjonalne ID>"}


JobId może być np. generowanym identyfikatorem zadania – choć w prostszej wersji możemy go pominąć, jeśli nie przewidujemy odpytywania statusu. Ważne, że po otrzymaniu takiej odpowiedzi workflow n8n (kafelek HTTP Request) zakończy się, a dalszy ciąg nastąpi, gdy dotrze callback do webhooka.
Następnie usługa w tle przetwarza audio i wysyła POST na podany callbackUrl z wynikiem transkrypcji. (Szczegóły formatu wyniku – patrz niżej).

Tryb synchroniczny (brak callback): Serwis wykonuje transkrypcję w ramach bieżącego żądania i po ukończeniu zwraca bezpośrednio wynik transkrypcji jako JSON. Ten tryb jest użyteczny dla krótkich nagrań lub testów, ale w kontekście n8n musimy uważać na timeouty. N8n (oraz pośrednie serwery) mają limity czasu na wykonanie HTTP requestu. Jeśli transkrypcja potrwa zbyt długo (np. kilkadziesiąt sekund lub więcej), może dojść do zerwania połączenia. Dlatego w praktyce rekomendujemy użycie trybu asynchronicznego z callbackiem, zwłaszcza dla dłuższych plików, aby “bez timeoutów obsłużyć długie nagrania”
n8n.io
n8n.io
.

(Opcjonalnie) GET /models lub GET /status/{jobId}: To nie jest niezbędne w MVP, ale rozważyć można endpoint do sprawdzania dostępnych modeli lub statusu danego zadania. Na razie jednak plan zakłada prostą architekturę: albo wynik wraca callbackiem, albo bezpośrednio, więc dodatkowe sprawdzanie statusu nie jest wymagane.

Format danych wyjściowych (transkrypcja):

Aby ułatwić integrację, zaprojektujemy wynik w takim formacie, jaki oczekuje obecny workflow (możliwie zbliżony do tego, co zwracał VLM Run). W ten sposób minimalizujemy zmiany w logice n8n (np. w tworzeniu dokumentu Google).

Proponowany format wyniku transkrypcji (JSON), wysyłany w ciele callbacka lub odpowiedzi synchronicznej:

{
  "response": {
    "segments": [
      {
        "start_time": <float>, 
        "end_time": <float>, 
        "content": "<tekst segmentu 1>"
      },
      {
        "start_time": <float>,
        "end_time": <float>,
        "content": "<tekst segmentu 2>"
      }
      // ... kolejne segmenty
    ],
    "metadata": {
      "duration": <całkowity czas nagrania w sekundach (number)>,
      "language": "<język rozpoznany (opcjonalnie)>",
      "model": "<użyty model/poziom Whisper>",
      "confidence": <średnie zaufanie/modelu, jeśli dostępne>
    }
  },
  "completed_at": "<timestamp ukończenia>",
  "error": null
}


Pole segments: lista segmentów tekstu z znacznikami czasowymi. Każdy segment ma początek i koniec (sekundy, np. z dokładnością do części sekundy) oraz rozpoznany tekst. Biblioteka Whisper generuje takie segmenty automatycznie – np. co kilka sekund, z podziałem na zdania. Wykorzystamy je, aby móc w dokumencie Google wstawić czytelne bloki tekstu z czasami. (Dokładnie tak zrobił workflow VLM Run – iterował po segmentach i wypisywał je z znacznikami czasu【37†】).

metadata: dodatkowe informacje o transkrypcji:

duration – czas trwania audio. Uwaga: faster-whisper udostępnia metadane, z których można pobrać długość nagrania, co zapiszemy tu. Wykorzystujemy to np. by w dokumencie Google zapisać Total Duration.

language – rozpoznany język (Whisper rozpoznaje język, możemy go zwrócić dla informacji).

model – np. nazwa/model użytego modelu Whisper (dla logów; np. "Whisper Tiny", "Whisper Base En").

confidence – jeśli dostępne średnie confidence lub jakieś metryki (opcjonalne).

completed_at: znacznik czasowy kiedy zakończono transkrypcję. W przykładzie użyto tego, by wstawić datę/godzinę w raporcie (patrz template tekstu w Google Docs node: {{ new Date($json.body.completed_at)... }})【37†】. Format może być np. ISO 8601.

error: pole na ewentualny komunikat błędu. Przy sukcesie będzie null lub nieobecne. (Pozwala to webhookowi/GoogleDocs rozpoznać, czy transkrypcja się powiodła).

Przykład użycia:
Jeśli n8n wyśle żądanie:

POST http://localhost:8000/transcribe?callback=https://n8n-instance/webhook/xyz123 


z załączonym plikiem audio, serwis:

Natychmiast odpowie: {"status":"processing"} (kod 202 Accepted) – co pozwoli zakończyć etap HTTP Request w n8n.

Rozpocznie transkrypcję w tle. Po powiedzmy 30 sekundach, gdy zakończy:

Wyśle POST https://n8n-instance/webhook/xyz123 z body zawierającym JSON jak wyżej (response.segments, metadata, etc.).

Ten webhook wywoła w n8n drugi segment workflow (node Receive Transcription Results), który następnie przekaże dane do Google Docs node w celu utworzenia raportu.

Implementacja (wskazówki):

Plik docker/whisper_local/app/main.py należy uzupełnić o powyższą logikę. Podczas rozmowy rozważaliśmy użycie biblioteki fastapi wraz z mechanizmem BackgroundTasks do obsługi zadania w tle (asynchroniczna transkrypcja). Kilka wskazówek przy implementacji:

Należy załadować model Whisper przy starcie (np. w globalu aplikacji, aby nie ładować przy każdym żądaniu). faster-whisper umożliwia wczytanie modelu – domyślnie może to być model base. Wymagania (requirements.txt) zawierają tę bibliotekę【39†】, więc środowisko jest gotowe.

Endpoint POST /transcribe powinien przyjmować plik. W FastAPI można to zadeklarować jako parameter typu file: UploadFile = File(...). Trzeba też dodać from fastapi import File, UploadFile, BackgroundTasks.

Jeżeli callbackUrl jest podany (można pobrać go np. jako parametr query: callbackUrl: str = None w funkcji endpointu), to:

Odczytujemy plik (np. file.file.read() aby uzyskać bytes audio, albo przekazujemy dalej strumień do modelu).

Uruchamiamy zadanie w tle: BackgroundTasks.add_task() z funkcją, która wykona transkrypcję i wykona requests.post(callbackUrl, json=wynik). Można też wykorzystać wbudowane mechanizmy AsyncIO, ale użycie wbudowanego background task z FastAPI jest prostsze.

Zwracamy natychmiast odpowiedź {"status":"processing"}. Kod HTTP 202 jest wskazany.

Jeśli callbackUrl nie podano, wtedy możemy wykonać transkrypcję synchronnie i zwrócić wynik bezpośrednio (kod 200). Uwaga: Ten tryb raczej do testów – w środowisku produkcyjnym użyjemy callback, by nie blokować n8n.

Transkrypcja z faster-whisper: Trzeba zainicjować model, np.

model = WhisperModel("medium", device="cpu") 


(rozmiar modelu zależny od możliwości – tiny, base, medium, large – medium zapewni lepszą jakość kosztem prędkości). Jeśli dostępny GPU, można dodać device="cuda" i ewentualnie compute_type="float16" dla przyspieszenia.
Następnie:

segments, info = model.transcribe(audio_bytes, language="pl")


gdzie segments to generator lub lista segmentów (start, end, text), a info zawiera m.in. długość nagrania, wykryty język itp. Trzeba z tego złożyć nasz wynik JSON zgodnie ze specyfikacją. Np. iterujemy po segmentach:

result_segments = []
for segment in segments:
    result_segments.append({
        "start_time": segment.start, 
        "end_time": segment.end, 
        "content": segment.text
    })


i przygotowujemy result = {"response": {"segments": result_segments, "metadata": { "duration": info.duration, "language": info.language, "model": "Whisper Medium" }}, "completed_at": datetime.utcnow().isoformat(), "error": None}.

Po otrzymaniu tak przygotowanego result:

Jeśli działa w tle (jest callbackUrl): wysyłamy requests.post(callbackUrl, json=result). Można dodać nagłówek Content-Type: application/json choć requests przy json= to załatwi.

Jeśli bez callback: zwracamy tę strukturę jako odpowiedź FastAPI.

Obsługa błędów: Warto owinąć transkrypcję w try/except. Jeśli wystąpi wyjątek (np. uszkodzony plik audio), serwis może zwrócić HTTP 500 lub w trybie async wysłać callbacka z polem "error": "<opis błędu>". Workflow n8n powinien umieć to obsłużyć (np. webhook mógłby przekazać błąd dalej, a Google Docs node mógłby pominąć tworzenie raportu jeśli jest error – to kwestia do ewentualnego zaimplementowania logicznie w n8n).

Bezpieczeństwo: Ponieważ ta usługa będzie raczej działać lokalnie (n8n i serwis transkrypcji na tej samej maszynie/ sieci), nie dodajemy na razie uwierzytelniania. Gdyby kiedyś była wystawiona publicznie, należałoby pomyśleć o autoryzacji (np. token w nagłówku lub w URL callbacka).

Testy: Po zaimplementowaniu, warto przetestować samą usługę niezależnie: uruchomić docker-compose up (patrz niżej) i np. użyć narzędzia typu cURL lub Postman, aby wysłać POST /transcribe z małym plikiem audio. Sprawdzimy, czy odpowiedź przychodzi i/lub czy callback (można zastąpić własnym tymczasowym endpointem testowym) otrzymuje dane.

(Powyższa treść stanowi propozycję zawartości pliku transcription_api_spec.md – opisuje on projekt API naszego serwisu transkrypcji.)

Workflow n8n – opis i dostosowanie (n8n_workflow_notes.md)

W pliku cursor/CONTEXT/n8n_workflow_notes.md zgromadzimy notatki na temat integracji workflow z usługą transkrypcji. Celem jest opisanie logiki przepływu oraz wskazanie, jak zostało to zaimplementowane w n8n, tak aby repozytorium dokumentowało działanie całego systemu.

Opis przepływu (workflow) transkrypcji:

Monitorowanie skrzynki e-mail (Gmail Trigger):
Workflow rozpoczyna się od kafelka Gmail Trigger, skonfigurowanego do nasłuchiwania nowych wiadomości e-mail z określonymi cechami (np. w określonej skrzynce/etykiecie, zawierających załączniki audio). Gdy przychodzi nowa wiadomość spełniająca kryteria, node ten inicjuje wykonanie przepływu.
Ustawienia: W Gmail Trigger można określić m.in. filtrowanie po nadawcy, temacie lub czy e-mail ma załącznik. W naszym przypadku interesują nas maile z plikami audio – np. zastosujemy filtr has:attachment i ograniczymy formaty (to może być realizowane węzłem później, ale Gmail API może zwrócić tylko metadane, więc dodatkowy filtr w kodzie/n8n może sprawdzać nazwę pliku).
Pobieranie pliku: Gmail Trigger domyślnie zwraca treść maila i meta danych. Aby uzyskać zawartość załącznika, można użyć następujących strategii:

W opcjach Gmail Trigger włączyć pobieranie załączników (jeśli taka opcja istnieje; w niektórych wersjach Gmail node jest opcja Download Attachments). To sprawi, że node od razu wypluje binarne dane pliku w swoim output.

Jeśli powyższa opcja nie jest dostępna lub wygodna, alternatywą jest użycie węzła Google Drive: Gmail może automatycznie zapisywać załączniki na dysku (np. jeśli tak skonfigurujemy lub jeśli mail jest z Google Drive linkiem). Nasz wcześniejszy prototyp mywork.json wykorzystywał node Google Drive - Download file zaraz po Gmail, co wskazuje, że tamten przepływ zakładał obecność ID pliku na Drive do pobrania【23†】. W uproszczeniu przyjmijmy, że Gmail Trigger będzie bezpośrednio dawać plik. Jeśli nie – można dodać krok pośredni do pobrania go (np. IMAP node lub Gmail > Drive).

W niniejszym workflow zakładamy konfigurację, gdzie Gmail Trigger dostarcza binaria załączników (np. w polu attachments lub podobnym).

Po uruchomieniu triggera, dane (zwłaszcza plik audio) są przekazywane dalej do następnego etapu.

Wysłanie audio do transkrypcji (HTTP Request do lokalnego API):
Zamiast dedykowanego kafelka VLM Run (jak w oryginalnym szablonie), używamy węzła HTTP Request w trybie POST, aby przesłać plik audio do naszej usługi transkrypcji (działającej na localhost:8000).
Kluczowe ustawienia tego kafelka:

URL: http://localhost:8000/transcribe – z dodaniem parametru callback. Skorzystamy z możliwości n8n do dynamicznego wstawienia URL webhooka:

Najpierw konfigurujemy nasz Webhook node (o nim w kroku 3) z unikalną ścieżką, np. /transcription_result. Gdy workflow jest aktywny, n8n wygeneruje pełny URL (zawierający domenę i ewentualnie klucz autoryzujący) dla tego webhooka. Ten URL możemy pobrać wewnątrz workflow za pomocą wyrażeń.

W polu URL naszego HTTP Request ustawiamy:

http://localhost:8000/transcribe?callback={{$node["Receive Transcription Results"].webhookUrl}}


gdzie $node["Receive Transcription Results"].webhookUrl jest wyrażeniem n8n, które w momencie wykonania zostanie zastąpione pełnym adresem HTTP naszego webhooka oczekującego na wynik. Dzięki temu serwis transkrypcji będzie wiedział, gdzie odesłać odpowiedź.

Metoda: POST.

Body/Payload: Ponieważ wysyłamy plik binarny, w konfiguracji HTTP Request ustawiamy Send Binary Data = True. N8n pozwala wskazać, z którego poprzedniego nodu i której właściwości wziąć dane binarne. Jeśli Gmail Trigger udostępnił plik w np. właściwości attachments (jako tablica plików), wybieramy odpowiedni element (np. pierwszy załącznik) do wysłania.

Pole Content-Type powinno być ustawione automatycznie jako multipart/form-data przy wysyłaniu binariów (n8n tworzy form-data z plikiem). Jeśli trzeba, jawnie wskazujemy, że pole pliku to np. "file" i ewentualnie dodajemy inne pole tekstowe callbackUrl w zapytaniu. Alternatywnie, jak wspomniano, możemy po prostu przekazać callback jako parametr w URL (to uprości, bo wtedy ciało to tylko plik).

Headers: W typowej konfiguracji nie musimy dodawać specjalnych nagłówków (poza tym, co ustawi n8n dla form-data). Jeśli jednak wprowadzimy np. autoryzację to tutaj by się pojawiła – aktualnie nasz serwis nie wymaga tokenu, więc pomijamy.

Response: Ten node otrzyma natychmiastową odpowiedź z serwisu transkrypcji. Jeśli wszystko pójdzie dobrze, powinna to być {"status":"processing"} z kodem 202. Ponieważ nie planujemy wykorzystywać tej odpowiedzi dalej (workflow i tak czeka na webhook), możemy nie robić nic z wynikiem. Warto jednak obsłużyć ewentualne błędy:

Jeśli HTTP Request zwróci błąd (np. serwis nie odpowie, lub zwróci 500), możemy w n8n ustawić Retry lub Error Trigger. Na razie zakładamy, że serwis jest dostępny i błędy obsłużymy prostym logowaniem.

Połączenie: Gmail Trigger powinien być połączony do tego HTTP Request (to musimy upewnić się edytując workflow). W connections JSON będzie to np.:

"Monitor Email Attachments": {
  "main": [
    [ { "node": "Transcribe Audio (HTTP)", "type": "main", "index": 0 } ]
  ]
}


(Zakładamy nazwę nodu HTTP jako “Transcribe Audio (HTTP)” dla czytelności).

W wyniku wykonania tego nodu serwis transkrypcji rozpocznie pracę, a wątek n8n dla tej ścieżki de facto się zakończy (node HTTP Request zakończył pracę, kolejny node w tym łańcuchu brak – bo czekamy teraz na drugą ścieżkę).

Webhook – odbiór wyniku transkrypcji:
W workflow dodajemy kafelek Webhook (np. nazwany “Receive Transcription Results”), który posłuży do odbioru asynchronicznej odpowiedzi. Ten node działa jako trigger typu “Waiting Webhook” – co oznacza, że workflow będzie w gotowości nasłuchiwać na określonym endpointcie i dopiero po jego wywołaniu wykona kolejne kroki.
Konfiguracja:

Ustawiamy unikalny URL (path), np. /transcription_result. Jeśli instancja n8n jest prywatna, możemy użyć też opcji Listen to localhost jeśli serwis dzwoni z tego samego hosta (to zapobiega wystawianiu publicznego URL). W wielu wypadkach jednak webhook będzie miał adres publiczny (jeśli nasz n8n np. działa w chmurze) – wtedy serwis transkrypcji musi mieć do niego dostęp. Załóżmy, że są w tej samej sieci/dokkerze, więc localhost:5678/webhook/transcription_result może zadziałać (o ile n8n nasłuchuje na odpowiednim porcie i dopuszcza połączenia).

Ważne, by adres użyty w kroku 2 jako callback dokładnie zgadzał się z tym, co tu ustawimy. Uwaga: n8n generuje pełny URL zawierający m.in. ID wykonania workflow (tzw. executionId) jeżeli webhook jest ustawiony w trybie “Execute Workflow”. Alternatywnie można użyć trybu “Generic Webhook” bez id, ale wtedy obsługa w jednym workflow wielu równoległych transkrypcji jest trudniejsza (bo nie wiemy, do której transkrypcji odnosi się wynik).

Prawdopodobnie najlepszym wyborem jest Webhook w trybie “Execute Workflow” (pomocniczy) – wtedy n8n każdorazowo uruchomi nową instancję workflow dla przychodzącego webhooka. Jednak w naszym przypadku chcemy kontynuować ten sam workflow.

W praktyce, w oryginalnym przykładzie n8n, pewnie użyto mechanizmu, gdzie webhook kontynuuje to samo wykonanie (dlatego w URL jest ID). Sądząc po tym, że w parametrach Google Docs node wstawiamy $json.body..., co wskazuje na dane z webhooka, wygląda że to jedna ciągła wykonanie po pauzie.

W n8n Webhook node ma opcję “Response Mode: Last Node” lub “Respond Immediately”. Tutaj pewnie ustawiono Last Node, żeby odpowiedź na webhooka (do serwisu) nastąpiła dopiero po wygenerowaniu dokumentu (co może nie być potrzebne u nas). Można też webhookowi ustawić, by od razu odpowiadał np. 200 OK, a resztę robił asynchronicznie.

Powiązanie z serwisem: Gdy serwis transkrypcji wykona POST na ten webhook, przekaże JSON zgodny z poprzednią specyfikacją. Webhook node w n8n odbierze to i udostępni w swoich output data. Zazwyczaj dostęp do przesłanych danych jest poprzez:

$json.body – ciało żądania (jako obiekt, jeśli to JSON). Z naszego przykładu użycia: $json.body.response.segments i $json.body.response.metadata itp. właśnie tak będziemy odwoływać się do wyników w następnym nodzie (Google Docs).

Inne przydatne: $headers (gdybyśmy potrzebowali nagłówków) lub $query (gdyby parametry w URL były).

Połączenie: Webhook jest traktowany jako trigger nowej ścieżki. W edytorze n8n nie łączymy go z poprzednim HTTP Request (bo to osobna gałąź). Zamiast tego, łączymy Webhook do kolejnego węzła, którym jest Google Docs. To połączenie (Webhook -> Google Docs) zostało już uwidocznione w naszym JSON【24†】.

Generowanie raportu w Google Docs:
Ostatnim etapem jest utworzenie lub aktualizacja dokumentu w Google Docs z treścią transkrypcji. Używamy kafelka Google Docs (prawdopodobnie ustawionego na operację “Update” istniejącego dokumentu). Nasza rozmowa i dane z szablonu sugerują następującą konfigurację:

Autoryzacja: Node Google Docs wymaga poświadczeń OAuth do naszego Google konta. Należy w n8n dodać credential Google Docs OAuth2 i przypisać go w tym nodzie. (To będzie widoczne w JSON jako credentials: { googleDocsOAuth2Api: { id: "..."} } podobnie jak przy Drive/Gmail).

Dokument docelowy: Najlepiej przygotować wcześniej pusty dokument Google i skopiować jego URL. W nodzie w parametrze documentURL wstawiamy link do tego dokumentu【37†】. Dzięki temu node wie, który dokument edytować. (Alternatywnie można utworzyć nowy, ale łatwiej mieć szablon i go nadpisać).

Operacja: Ustawiamy na Update (aktualizuj dokument).

Action: W sekcji akcji konfigurujemy, co dokładnie zrobić. W naszym przykładzie z szablonu użyto akcji Insert – czyli wstawienia tekstu na końcu dokumentu (bądź w określonym miejscu, ale domyślnie doc appends). Przygotowano tam dość złożony tekst z użyciem szablonu markdown/HTML z osadzonymi danymi:

Wstawiany tekst zaczynał się od tytułu (emoji 📄 i “Audio Transcription Report”), potem data (🗓️ Date: ...) i czas trwania (⏱️ Total Duration: ... seconds). Datę sformatowano przy pomocy wbudowanej funkcji w n8n (JavaScript w backticks) – zauważ {{ new Date($json.body.completed_at).toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' }) }} w treści【37†】, co pobiera timestamp z webhooka i formatuje na czytelną datę.

Następnie kluczowa część: iteracja po segmentach transkrypcji:

{{ 
  $json.body.response.segments.map((segment, index) =>
    `\n🔹 Segment ${index + 1}\n` +
    `⏰ Time: ${segment.start_time.toFixed(2)}s → ${segment.end_time.toFixed(2)}s\n` +
    `📝 Transcript: "${segment.content.trim()}"\n`
  ).join('\n')
}}


To jest wplecione w tekst akcji Insert – node Google Docs pozwala wstawiać takie wyrażenia, które są wykonywane przy uruchomieniu. Powyższy kod dla każdego segmentu generuje blok tekstu zawierający numer segmentu, zakres czasu oraz sam tekst wypowiedzi, a wszystko formatowane z odpowiednimi emotikonami i nowymi liniami dla czytelności【37†】.

Całość node’a Generate Transcription Report powoduje, że do wskazanego dokumentu zostanie dopisana treść. (Jeśli chcemy za każdym razem nadpisywać zawartość dokumentu, można przed wstawieniem np. wyczyścić dokument – ale Google Docs node ma ograniczoną ilość akcji; być może w tym szablonie on dopisuje kolejno transkrypcje. Można też tworzyć nowy dokument per transkrypcja, w bardziej rozbudowanym scenariuszu).

Efekt: Po wykonaniu nodu treść dokumentu Google zostaje zaktualizowana i możemy ją podejrzeć w Google Drive.

Zakończenie workflow: Po tym kroku możemy uznać workflow za zakończony. Można dodać ewentualnie węzeł końcowy (np. powiadomienie e-mail z linkiem do dokumentu, lub jakąś logikę sprzątającą), ale to już rozszerzenia.

(Opcjonalnie) Dodatkowe kroki AI – analiza transkrypcji:
Podczas rozmowy rozważaliśmy wzbogacenie workflow o element analizy tekstu za pomocą modelu językowego (LLM). Np. po utworzeniu transkrypcji można:

Extractor akcji – dodać węzeł Information Extractor (z pakietu LangChain) do wyciągnięcia z transkrypcji określonych informacji (np. listy zadań, podsumowania rozmowy, kluczowych punktów). W naszym prototypie mywork.json taki node się pojawił, choć nie został w pełni skonfigurowany【23†】【32†】. Wymaga on zdefiniowania tzw. atrybutów do ekstrakcji wraz z promptami (pole parameters.attributes).

Automatyczne podsumowanie – ewentualnie węzeł Text Generation (też LangChain lub OpenAI node) w celu wygenerowania streszczenia całej transkrypcji.

Wykorzystanie wyników – wyniki analizy można zapisać do tego samego dokumentu (np. dopisując “Podsumowanie:” na końcu) lub wysłać gdzie indziej (np. e-mail z podsumowaniem, wiadomość Slack itp.).
Jeśli planujemy takie rozszerzenia, warto przygotować osobno prompty i logikę – poniżej (w sekcji Prompty AI) opisujemy wskazówki. Na ten moment, jednak, podstawowy workflow skupia się na dostarczeniu pełnej transkrypcji do dokumentu.

Uruchomienie i harmonogram:
Po skonfigurowaniu wszystkiego, uruchamiamy workflow w n8n (ustawiając go jako aktywny). Gmail Trigger będzie działał w tle na wybranym zakresie (np. sprawdzając co X minut nowe maile lub działając w push – zależnie od implementacji node’a). Możemy też workflow wywołać ręcznie (np. wgrać testowy plik, symulując trigger).
W środowisku produkcyjnym warto ustawić ograniczenia, np. by nie transkrybować zbyt dużej liczby maili równocześnie – ewentualnie Gmail trigger można ograniczyć do konkretnej etykiety i przenosić maile po przetworzeniu do innej (takie usprawnienie).
Nasze skrypty start_transcriber.bat i stop_transcriber.bat pomagają włączać/wyłączać serwis transkrypcji (poprzez docker-compose up/down
GitHub
GitHub
). Zakładamy, że plik docker-compose.yml został utworzony w katalogu głównym repo (jeśli nie, trzeba go dodać – patrz niżej). Ten serwis musi być uruchomiony, zanim workflow n8n odbierze e-mail, inaczej HTTP Request zakończy się błędem połączenia.

(Powyższe stanowi zawartość dla pliku n8n_workflow_notes.md – opisuje krok po kroku działanie workflow oraz wskazówki integracyjne.)

Uzupełnienie: plik docker-compose.yml

Aby dopełnić kompletność repozytorium, warto dodać (jeśli jeszcze nie ma) plik docker-compose.yml w katalogu głównym, ułatwiający uruchomienie lokalnej usługi transkrypcji. Nasze skrypty sugerują, że taki plik powinien istnieć (wywołanie docker-compose up -d/down w batchach). Jeśli nie został jeszcze utworzony, należy go stworzyć z treścią podobną do poniższej:

version: "3.8"
services:
  transcriber:
    build: ./docker/whisper_local
    container_name: whisper_transcriber
    ports:
      - "8000:8000"
    volumes:
      - ./docker/whisper_local/app:/app  # montowanie kodu (opcjonalnie, w trakcie dev)
    restart: unless-stopped


Ten plik buduje obraz z Dockerfile (ścieżka już w repo) i wystawia port 8000. Montowanie wolumenu pozwoli na szybkie iterowanie zmian w kodzie bez przebudowy (opcjonalnie). Po dodaniu tego pliku, polecenie start_transcriber.bat uruchomi nam usługę w tle.

(Dodanie docker-compose.yml nie było wprost w rozmowie wspomniane, ale jest to logiczne uzupełnienie repozytorium by wszystko zadziałało out-of-the-box.)

Lista zadań do realizacji (TASKS.md)

W pliku cursor/TASKS.md przedstawiamy listę konkretnych zadań wynikających z powyższych ustaleń. Zadania te prowadzą do uruchomienia pełnego rozwiązania i mogą służyć jako checklist dla dewelopera:

 Implementacja API transkrypcji w FastAPI: Uzupełnić docker/whisper_local/app/main.py o endpoint POST /transcribe realizujący opisane funkcje (odbiór pliku, transkrypcja przez Whisper, obsługa callback) oraz ewentualnie dodać obsługę błędów.

 Konfiguracja Docker: Utworzyć/uzupełnić docker-compose.yml w repozytorium, aby umożliwić łatwe uruchomienie serwisu transkrypcji komendą docker-compose up -d
GitHub
. Sprawdzić, czy obraz buduje się poprawnie (Python, FastAPI, model Whisper).

 Przygotowanie środowiska Google: Skonfigurować w n8n poświadczenia OAuth2 dla Gmaila i Google Docs. Uzyskać potrzebne Client ID/Secret z Google Cloud i połączyć konta:

Gmail Trigger: autoryzować dostęp do Gmail API (zakresy Gmail.readonly lub Gmail.modify, zależnie od implementacji nodu).

Google Docs: autoryzować API do edycji dokumentów (Google Drive/Docs API).
Zapisać credentials w n8n i przypisać je odpowiednim węzłom.

 Utworzenie dokumentu Google dla raportów: Stworzyć na Google Drive pusty dokument, który będzie służył jako szablon raportu transkrypcji. Skopiować jego URL i w workflow n8n (node Google Docs) wpisać ten URL w ustawieniach (parametr documentURL)【37†】. Upewnić się, że nasz OAuth ma uprawnienia do edycji tego dokumentu.

 Złożenie i import workflow n8n: Zaktualizować plik JSON workflow (lub złożyć go w edytorze graficznym) zgodnie z notatkami:

Dodać node Gmail Trigger (konfiguracja filtra na maile z audio).

Dodać node HTTP Request -> ustawienia URL z callback, binarny upload pliku.

Dodać node Webhook (patht /transcription_result, metoda POST, oczekuj JSON).

Dodać node Google Docs (update doc, wstawianie tekstu z wykorzystaniem danych z webhooka).

(Ewentualnie dodatkowe nod’y jak ekstrakcja informacji, jeśli planowane – na razie opcjonalne).

Połączyć: Gmail -> HTTP Request; Webhook -> Google Docs.

Zaimportować workflow do n8n i zapisać jako aktywny (nazwać np. "Audio Transcription Workflow").

 Test end-to-end: Uruchomić kontener transkrypcji (start_transcriber.bat), następnie przetestować cały przepływ:

Wysłać na skrzynkę Gmail testowy e-mail z plikiem audio (np. krótkie nagranie w formacie mp3).

Obserwować w n8n: Gmail Trigger powinien wykryć mail, przekazać plik do HTTP Request.

Sprawdzić logi/usługę: serwis powinien otrzymać żądanie (potwierdzenie w konsoli docker, log połączenia). Zwrócić 202.

Po kilkudziesięciu sekundach (czas transkrypcji) webhook w n8n powinien zostać wywołany – workflow przejdzie do Google Docs node.

Zweryfikować wynik: w docelowym Google Doc pojawia się transkrypcja wraz z segmentami czasu. Sprawdzić, czy tekst jest poprawny i format zgodny z oczekiwaniami.

 Obsługa błędów i wyjątków: Jeśli test się nie powiedzie, zdiagnozować:

brak połączenia do API (czy porty, URL się zgadza),

brak uprawnień (czy Gmail/Docs credentials poprawnie działają),

ewentualne błędy w formacie danych (czy serwis zwrócił dane w dokładnie takiej strukturze, jak używa Google Docs node – w razie różnic poprawić albo format, albo szablon w Docs node).

 Dokumentacja: Upewnić się, że wszystkie pliki dokumentacyjne w repo (TASKS.md, CONTEXT/*.md, PROMPTS.md, README.md) są uaktualnione i opisują aktualny stan systemu. Szczególnie, po implementacji, można:

Zaktualizować główny README.md – dopisać krótki opis projektu (bo obecnie to tylko „Skeleton repository for transcription service”).

Uzupełnić transcription_api_spec.md o ewentualne zmiany w trakcie implementacji (np. jeśli format wyniku się zmienił).

Dodać ewentualne uwagi o wydajności (np. który model Whisper jest używany, ile trwa transkrypcja dla 1 minuty audio, itp.).

 Rozszerzenia (przyszłe prace): Zanotować pomysły na rozbudowę:

Automatyczne streszczenie transkrypcji (dodanie node’a AI do generowania podsumowania).

Wykrywanie mówców (speaker diarization) – choć Whisper w podstawie nie rozpoznaje mówców, można łączyć z innymi narzędziami.

Integracja z innymi usługami – np. wysyłanie linku do dokumentu przez email albo Slack po skończeniu, zapisywanie transkryptu w bazie danych, itp.

Udoskonalenie frontendu – np. formularz który pozwoli ręcznie wrzucić plik audio do transkrypcji (alternatywa do monitorowania maila).

(Powyższe to zawartość pliku TASKS.md – lista kontrolna zadań potrzebnych do osiągnięcia w pełni działającego systemu).

Wytyczne dla agentów AI / prompty (AGENT_PROMPTS.md)

W ramach projektu możemy wykorzystywać model GPT/LLM (np. poprzez węzły LangChain w n8n) do wyższych funkcji, takich jak podsumowywanie transkryptu czy ekstrakcja danych. Plik cursor/PROMPTS/AGENT_PROMPTS.md będzie zawierał wytyczne odnośnie projektowania promptów dla takich agentów AI, aby uzyskać odpowiednie wyniki i zintegrować je z resztą systemu.

Zasady tworzenia skutecznych promptów (poleceń) dla AI w kontekście transkrypcji audio:

Jasno określony cel: Każdy prompt powinien wyraźnie komunikować modelowi, co ma zrobić z dostarczonym tekstem transkrypcji. Np. "Streść poniższą transkrypcję spotkania w 5 punktach bullet." lub "Wymień wszystkie ustalenia i przypisane zadania wraz z terminami, które pojawiają się w transkrypcji." Unikamy ogólników – konkretne polecenie ułatwia uzyskanie pożądanego rezultatu.

Kontekst i format odpowiedzi: Warto w promptach podać kontekst (np. "Poniżej znajduje się transkrypcja rozmowy biznesowej. Twoim zadaniem jest ...") oraz oczekiwany format odpowiedzi ("Odpowiedź w formie listy:" lub "Udziel odpowiedzi po polsku, pełnymi zdaniami."). Model wtedy wie, jak ma sformatować wynik.

Unikanie halucynacji / trzymanie się faktów: W przypadku pracy z transkrypcją kluczowe jest, by model nie dodawał od siebie informacji, których nie ma w tekście. Można to wymusić poprzez instrukcje w stylu: "Odpowiadaj tylko na podstawie dostarczonej transkrypcji. Jeśli czegoś w niej nie ma, napisz 'Brak informacji'. Nie dodawaj żadnych informacji spoza transkrypcji."

Limity i objętość: Transkrypcje mogą być długie, co stanowi wyzwanie dla modeli (ograniczenie tokenów). Dla dłuższych zapisów (np. godzinna rozmowa) dobrze jest dzielić tekst na części i przetwarzać sekwencyjnie lub używać wyspecjalizowanych narzędzi (LangChain może pomóc w podzieleniu i z pamięcią konwersacji). Prompt powinien ewentualnie zawierać instrukcje radzenia sobie z długością: "Jeśli tekst jest zbyt długi, streść każdą część oddzielnie."

Przykłady (few-shot): Jeżeli chcemy bardzo precyzyjnego wyniku, można w promptcie zawrzeć przykład wejścia i oczekiwanego wyjścia. Np. "Przykład:\nTranskrypcja: '...'\nPolecenie: Wypisz daty.\nOdpowiedź: 12 czerwca 2023\n**\nTeraz właściwe zadanie: ..."* – choć to wydłuża prompt, może poprawić trafność.

Język poleceń: Warto zwrócić uwagę, że jeśli transkrypcja i końcowy odbiorca są w języku polskim, prompt także powinien być po polsku, by model wygenerował polską odpowiedź. W naszych scenariuszach będziemy formułować prompty w języku polskim dla spójności (chyba że korzystamy z modelu słabo radzącego sobie z PL – wtedy można poprosić o odpowiedź po angielsku, ale to raczej nie dotyczy nowoczesnych modeli).

Przykładowe prompty dla naszego use-case:

Podsumowanie spotkania:
Polecenie: "Zostałeś poproszony o przygotowanie podsumowania rozmowy na podstawie poniższej transkrypcji. Wypunktuj najważniejsze ustalenia i wnioski (maksymalnie 5 punktów). Użyj zwięzłego języka."
Użycie: do wygenerowania sekcji "Podsumowanie" po transkrypcji. Można to wstawić do nodu tekstowego (np. OpenAI) tuż po otrzymaniu transkryptu, a wynik dołączyć do dokumentu.

Wykrycie zadań i terminów:
Polecenie: "Przeanalizuj poniższą transkrypcję i wypisz wszystkie zadania do wykonania (action items) wraz z terminami (jeśli zostały określone). Podaj je w punktach, zaczynając od osoby odpowiedzialnej, następnie zadanie i termin."
Cel: ułatwienie wyciągnięcia z rozmowy kto, co ma zrobić i do kiedy. Taki prompt może być użyty z nodem Information Extractor, definiując atrybuty: np. tasks gdzie promptem jest powyższe polecenie.

Ekstrakcja słów kluczowych:
Polecenie: "Wypisz 5 słów kluczowych, które najlepiej oddają tematykę rozmowy, na podstawie transkrypcji."
Cel: tagowanie lub kategoryzacja rozmów (np. meeting tags, tematy).

Tłumaczenie transkrypcji: (jeśli potrzebne)
Polecenie: "Przetłumacz poniższą transkrypcję z języka polskiego na angielski. Zachowaj format akapitów."
Cel: uzyskanie wersji angielskiej, gdyby projekt tego wymagał (np. międzynarodowe udostępnienie). Węzeł OpenAI z GPT radzi sobie z tłumaczeniem.

Wykorzystanie w n8n: W praktyce, prompty te wprowadzamy w odpowiednich kafelkach:

Dla LangChain Information Extractor: konfigurujemy atrybuty. Np. atrybut "Zadania" z promptem jak wyżej o action items. Model (np. GPT-4) wygeneruje strukturę JSON z tymi informacjami, którą node zwróci.

Dla OpenAI node: można bezpośrednio wkleić tekst transkrypcji + prompt w jedno polecenie, ale lepiej użyć mechanizmu czatu: ustawić System Message z rolą i poleceniem ogólnym, a User Message dać transkrypcję z konkretnym pytaniem. Wtedy model otrzymuje to z podziałem ról.

Notatki dotyczące promptów: Ponieważ transkrypcja jest automatyczna, może zawierać błędy lub nieoznaczone role rozmówców. W promptach możemy więc zaznaczyć, że "transkrypcja może zawierać błędy, imiona własne mogą być niepoprawne – postaraj się je skorygować na podstawie kontekstu" – model czasem potrafi poprawić oczywiste literówki czy imiona.

(Zawartość powyższa jest przeznaczona do pliku AGENT_PROMPTS.md – zawiera zasady i przykłady tworzenia promptów dla AI w ramach naszego projektu.)

Podsumowanie i kolejne kroki

Po wprowadzeniu powyższych aktualizacji, repozytorium audioT (transcriptoonAI) będzie kompletne i gotowe do rozwijania kolejnych funkcjonalności. Mamy zdefiniowane:

Pełną dokumentację procesu (od specyfikacji API, przez opis workflow, listę zadań, po wskazówki dot. AI).

Szkielet kodu i konfiguracji (Docker, FastAPI, pliki workflow) do implementacji i uruchomienia systemu.

Następnym krokiem jest realizacja zadań implementacyjnych z TASKS.md – szczególnie napisanie kodu transkrypcji oraz skonfigurowanie i przetestowanie workflow w n8n. Gdy to zrobimy, będziemy dysponować działającym rozwiązaniem: wrzucenie pliku audio do skrzynki e-mail automatycznie wygeneruje transkrypt w Google Docs, bez potrzeby ręcznej pracy.

Dalsza praca może skupić się na doskonaleniu jakości (np. użycie większego modelu Whisper dla dokładności, dodanie mechanizmów filtrujących szumy), skalowalności (uruchomienie na serwerze z GPU, kolejkowanie zadań) oraz rozszerzeniach funkcjonalnych (jak wspomniane podsumowania, powiadomienia, integracje z innymi usługami). Dzięki dobrze udokumentowanemu repozytorium, każdy członek zespołu lub przyszły kontrybutor będzie mógł łatwo zrozumieć architekturę rozwiązania i kontynuować jego rozwój.