# PRD – Uutisagentti / Podcast backlog GitHubissa

## 1. Tavoite
Agentti kerää Agile / Arkkitehtuuri / Pilvi -uutisia ja tapahtumia, luokittelee ja pisteyttää ne, ja avaa niistä **ehdotus-issueita GitHubiin**. Kaikki jatko (hyväksyntä, labelointi tarkemmin, priorisointi, linkitys jaksoihin) tapahtuu GitHubin puolella.

---

## 2. Scope / MVP
- CronJob (K8s baremetal, hallinta Terraformilla) ajaa agentin säännöllisesti (esim. 1×/vrk).  
- Lähteiden lista konfiguroitavissa (`sources.yaml`).  
- Kerää uutiset RSS/HTTP:stä.  
- Poistaa duplikaatit (hash + similariteetti).  
- Luokittelee 4 teemaan: Agile, DevOps, Architecture/Infra, Leadership.  
- Summarointi: TL;DR + 2–3 bulletia *“mitä tämä tarkoittaa tiimille”*.  
- Luo GitHub Issue ehdotuksen:  
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
- Agentti pisteyttää ja järjestää aiheet kuukausinäkymää (seuraavat 4 viikkoa) varten.  
- Tuottaa analyysin tiedostoon `docs/analysis/situational-YYYY-MM.md`:  
  - Kuukauden yleiskuva, top-N lista perusteineen  
  - Kategoriatasapaino (Agile/DevOps/Architecture/Leadership)  
  - Suositellut aiheet viikoille 1–4 (deterministinen jako)  
- Pisteytyssignaalit: tuoreus (ajan vaimennus 4 viikkoa), lähteen auktoriteetti, uutuusarvo vs. viime kuukaudet, mahdolliset engagement-signaalit (jos saatavilla), kategoriabalanssi.  
- Konfiguroitava suunnitteluhorisontti: oletus 4 viikkoa.  
- Analyysi voidaan commitoida repo:on (konfiguroitavissa, dry-run tuettu).  

---

## 7. Roadmap
- **Vko 1:** RSS-fetch + `issues.md` generointi → manuaalinen luonti GitHubiin.  
- **Vko 2:** Summarointi + luokittelu + dedupe.  
- **Vko 3:** Terraform-projekti ja CronJobin määrittely Terraformilla K8s baremetal -klusteriin; viittaukset ulkoisiin Secrets/ConfigMappeihin muuttujien kautta.  
- **Vko 4:** GitHub API -integraatio → suorat draft-issuet backlogiin.  
