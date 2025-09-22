# PRD – Uutisagentti / Podcast backlog GitHubissa

## 1. Tavoite
Agentti kerää Agile / Arkkitehtuuri / Pilvi -uutisia ja tapahtumia, luokittelee ja pisteyttää ne, ja avaa niistä **ehdotus-issueita GitHubiin**. Kaikki jatko (hyväksyntä, labelointi tarkemmin, priorisointi, linkitys jaksoihin) tapahtuu GitHubin puolella.

---

## 2. Scope / MVP

Agentin toiminta jakautuu kahteen päävaiheeseen: jatkuvaan artikkelien keräämiseen ja kuukausittaiseen issue-generointiin.

### Vaihe 1: Artikkelien kerääminen ja prosessointi
- CronJob (K8s baremetal, hallinta Terraformilla) ajaa agentin säännöllisesti (esim. 1×/vrk).
- Agentti hakee uudet artikkelit `sources.yaml`-tiedostossa määritellyistä RSS/HTTP-lähteistä.
- Jokainen artikkeli prosessoidaan putkessa:
  - **Normalisointi:** Sisältö siistitään ja jäsennetään.
  - **Duplikaattien poisto:** Duplikaatit tunnistetaan ja poistetaan (hash + similariteetti).
  - **Rikastaminen:** Artikkeli luokitellaan yhteen neljästä teemasta (Agile, DevOps, Architecture/Infra, Leadership) ja siitä luodaan tiivistelmä (TL;DR + "mitä tämä tarkoittaa tiimille").
- Prosessoidut artikkelit tallennetaan persistoivaan **kuukausittaiseen data-arkistoon**, joka kerää potentiaalisia aiheita kuukauden aikana.

### Vaihe 2: Kuukausittainen issue-generointi
- Kuukausittain (tai triggeristä) käynnistyy erillinen työnkulku, joka lukee kaikki kuukauden aikana kerätyt artikkelit data-arkistosta.
- **Priorisointi ja suodatus:** Korkean prioriteetin artikkelit valitaan pisteytyksen perusteella.
- **Ryhmittely:** Toisiinsa liittyvät artikkelit ryhmitellään yhtenäisiksi aihekokonaisuuksiksi.
- **Ryhmien duplikaattien poisto:** Ryhmiä verrataan keskenään, jotta vältetään päällekkäisten issue-ehdotusten luominen.
- **Issueiden luonti:** Jokaisesta uniikista, korkean prioriteetin ryhmästä luodaan yksi formatoitu GitHub-issue. Issue sisältää tiivistelmät kaikista ryhmään kuuluvista artikkeleista.
- Issueiden luonti tapahtuu eräajona.

Alkuperäinen GitHub Issue -ehdotus:
  - **Title:** `[ARCH] Consumer-Driven Contract Testing`
  - **Labels:** `draft, agile|devops|architecture|leadership`
  - **Body:**
    - Lähteen tiivistelmä
    - “Impact to teams” -bulletit
    - Linkit alkuperäiseen
    - Suositus: “Sopii keskiviikon Architecture & Infra -jaksoon”

---

## 3. Non-functional requirements
- **Alusta:** K8s baremetal, ilman ingressiä.  
- **Infra-as-Code:** Kubernetes-resurssit hallitaan Terraformilla (kubernetes/helm-providerit). CronJob määritellään Terraformissa; `kubectl apply` ei käytössä.  
- **Integraatio:** GitHub API (PAT token Secretinä).  
- **Ajot:** cronjob → esim. klo 06:00 UTC joka aamu.  
- **Tulokset:** vain Issueiden luonti; kaikki hyväksyntä/workflow jatkuu GitHubissa.  
- **Resurssit:**
  - **Kehitys (lokaali):** Sisällön prosessointi paikallisella Ollama-instanssilla.
  - **Tuotanto (k8s):** Sisällön prosessointi Gemini Flash Cloud API:n kautta.

- **AI-backendit:** Vain kaksi tuettua vaihtoehtoa: Ollama (kehitys) ja Gemini Flash (tuotanto, Google AI Studio API). Ei HuggingFace/transformers tms.
- **Konfigurointi ja salaisuudet:** Kaikki Kubernetes Secrets ja ConfigMapit (mm. imagePullSecrets, sovelluksen ympäristömuuttujat, `sources.yaml`) luodaan ja omistetaan organisaation ulkopuolisissa prosesseissa (ops). Tässä repossa oleva Terraform ainoastaan VIITTAA niihin nimillä (esim. `image_pull_secret_name`, `app_env_configmap_name`, `sources_configmap_name`). Mitään salaisuuksien arvoja tai konfiguraation sisältöä ei tallenneta koodiin eikä Terraform-tilaan.

---

## 4. Ei scopea MVP:ssä
- Ei hyväksyntälogiikkaa agentissa.  
- Ei Issueiden muokkausta/sulkemista.  
- Ei Slack/Teams-notifikaatioita (voi lisätä jatkossa).  

---

## 5. Deliverables
- `sources.yaml` (lähteet ja avainsanat).  
- Terraform-konfiguraatio CronJobille (kubernetes/helm; ajastus + container), sisältäen tarvittavat resurssit: `Namespace` (tarvittaessa), `ServiceAccount`, `Secret` (GitHub PAT).  
  - HUOM: `imagePullSecrets` ja ConfigMap-viittaukset (app env, `sources.yaml`) määritellään muuttujina ja viitataan olemassa oleviin resursseihin; niiden luonti tapahtuu repo:n ulkopuolella.  
- Python-skriptit: fetch → normalize → dedupe → classify → summarize → create_issue.  
- Dokumentaatio: README (deployment + GitHub token konfigurointi).  
- GitHub Issue -template (malli, jota agentti käyttää).  

---

## 6. Priorisointi ja kuukausikohtainen tilanneanalyysi
- Kuukausittainen prosessi muuttaa kerätyn data-arkiston sisällön konkreettisiksi GitHub issue-ehdotuksiksi.
- **Syöte:** Työnkulku käyttää koko kuukauden data-arkistoa.
- **Pisteytys ja suodatus:** Artikkelit pisteytetään ja priorisoidaan tulevaa 4 viikon suunnitteluhorisonttia varten. Signaaleja ovat tuoreus (vaimennus), lähteen auktoriteetti, uutuusarvo ja kategoriatasapaino.
- **Ryhmittely ja eräajo:**
  - Korkean prioriteetin artikkelit ryhmitellään aihepiireittäin.
  - Ryhmistä poistetaan duplikaatit uniikkien ehdotusten varmistamiseksi.
  - Uniikeista ryhmistä valmistellaan eräajo issueiden luomiseksi.
- **Ensisijainen tuloste: GitHub Issuet:** Prosessin päätavoite on luoda draft-issueita GitHubiin valmiina jatkokäsittelyä varten.
- **Toissijainen tuloste: Tilanneanalyysi:** Prosessin sivutuotteena generoidaan yhteenveto tiedostoon `docs/analysis/situational-YYYY-MM.md`. Tämä tiedosto sisältää:
  - Yleiskatsauksen kuukauden aiheista.
  - Kategoriatasapainon (Agile/DevOps/Architecture/Leadership).
  - Listan suositelluista aiheista ja artikkeli-ryhmistä, joista ne muodostuivat.
- Pisteytyssignaalit: tuoreus (ajan vaimennus 4 viikkoa), lähteen auktoriteetti, uutuusarvo vs. viime kuukaudet, mahdolliset engagement-signaalit (jos saatavilla), kategoriabalanssi.
- Konfiguroitava suunnitteluhorisontti: oletus 4 viikkoa.
- Analyysi voidaan commitoida repoon (konfiguroitavissa, dry-run tuettu).

---

## 7. Roadmap
- **Vko 1:** RSS-fetch + `issues.md` generointi → manuaalinen luonti GitHubiin.  
- **Vko 2:** Summarointi + luokittelu + dedupe.  
- **Vko 3:** Terraform-projekti ja CronJobin määrittely Terraformilla K8s baremetal -klusteriin; viittaukset ulkoisiin Secrets/ConfigMappeihin muuttujien kautta.  
- **Vko 4:** GitHub API -integraatio → suorat draft-issuet backlogiin.  
