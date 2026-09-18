# Regola di Sviluppo: Pulizia e Isolamento Dati di Test

1. **Nessuna contaminazione del database principale**:
   Il database operativo `database/personale.db` non deve MAI conservare record fittizi, corsi di prova (non-CIFIGE) o dati matricolari generati durante l'esecuzione di test unitari o verifiche automatiche.

2. **Isolamento dei Test**:
   - I test unitari devono usare database SQLite separati/in-memory oppure ripulire rigorosamente i dati creati tramite metodi `tearDown`.
   - All'uscita delle suite di test, il database principale deve tornare allo stato legittimo contenente esclusivamente i corsi ufficiali approvati.

3. **Cancellazione dati fittizi**:
   Qualora un test o uno script inserisca dati provvisori, deve essere eseguita immediatamente una query mirata di eliminazione di tali record alla conclusione dell'attività.

