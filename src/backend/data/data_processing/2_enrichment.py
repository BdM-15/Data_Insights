"""
Step 2: Data Enrichment for USASpending Contract Data (ETL Pipeline Version)

This script performs cross-table enrichment and KBR/affiliate flagging for deduplicated tables.
It ensures both the prime awards and subawards tables have the following boolean flags, using only UEI logic:

Prime Awards Table (usaspending_prime_awards_enriched):
    - kbr_prime: TRUE if recipient_uei is in UEI_LIST (KBR was the prime contractor)
    - kbr_as_sub: TRUE if this recipient_uei ever appears as subawardee_uei in any subaward (KBR was a sub to someone else on any contract)
    - kbr_sub_issued: TRUE if this contract_award_unique_key ever appears as prime_award_unique_key in any subaward (this prime issued a subaward to any sub)

Subawards Table (usaspending_subawards_enriched):
    - kbr_prime: TRUE if the joined prime's recipient_uei is in UEI_LIST (KBR was the prime for this subaward)
    - kbr_as_sub: TRUE if subawardee_uei is in UEI_LIST (KBR was the subawardee on this subaward row)
        - Note: kbr_as_sub is now determined per deduplicated subaward row using subaward_unique_key, so each subawardee_uei is only flagged once per unique subaward event.
    - kbr_sub_issued: TRUE if the joined prime's recipient_uei is in UEI_LIST and the subawardee is not KBR (KBR issued a subaward to a non-KBR sub)

Additional enrichment:
    - All columns from the prime table are joined into the subawards table (with 'prime_' prefix as needed, except for join key).
    - subaward_unique_key is preserved from the deduplication process for traceability and batching.

This logic enables downstream analytics to distinguish:
    - Where KBR is a prime, a sub, or both
    - Where KBR self-performs (no subaward issued) vs. where KBR issued subawards
    - Where KBR was a sub to another prime
    - Each subaward event is uniquely identified and deduplicated using subaward_unique_key

All logic is implemented using efficient SQL subqueries and joins, and is fully modular for ETL orchestration.

Input: *_dedup tables in s2_interim schema (with subaward_unique_key carried over)
Output: *_enriched tables in s2_interim schema
"""

import os
import sys
import time
import logging
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

pg_user = os.getenv('PG_USER')
pg_password = os.getenv('PG_PASSWORD')
pg_host = os.getenv('PG_HOST')
pg_port = os.getenv('PG_PORT')
pg_dbname = os.getenv('PG_DBNAME')

db_url = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_dbname}"
engine = create_engine(db_url, echo=False)

logger = logging.getLogger(__name__)


# KBR/affiliate UEI list (provided by user)
UEI_LIST = [
    "XHHKVBDUP7R7", "SJ3QANR912G1", "JLSPHGZAF8L6", "S2MGFVL4HBL5", "WE11DMUYFR78", "LQGKFHF5GPX3", "W62YK6JFBJ28", "X4Z6XB7P2B95", "TWGDVBNK8LS7", "SCAHJH4FK963", "QRFKN8FEW498", "KJMYKBBNPU43", "ZM5WSGWLU463", "CKWAM5SJ3LK9", "ME4QS8H2KVX3", "GVLUCB2UX283", "JWK8UZM4WL51", "XNYZKKKJS698", "H7AJRBSDAAB3", "MAWLPJ3BGGL6", "FYDWBRMLRJM7", "C1F3PCZ648T3", "M6MUL8P5GNR7", "FPH1KB2KZSZ8", "KVC9Z1B19AY5", "KPVDRF17NW72", "UCF2ZAF3TD81", "CAEVQ5LJDJ43", "QWBYGNFNT4T6", "UF7GLXU2DEH5", "VKF1DSWRNK27", "TAG1WEXVRLT1", "F6G4L8SJ2UW3", "LCACMNJ44LA5", "TGQRD3UGFPR9", "V3M7LMQMXWT3", "G9HUM7929KT7", "ZUZ5MU8W2EK2", "H4JZA4SFLJT1", "NN4ARC7E4SP7", "C158H578Y149", "MG76VDBB7HT8", "RYDLKTFHJNE1", "FV9WW8AP1NB3", "NHMQSLZ6DFB9", "Y32CU9FBJDR8", "PULAGF1NFNY1", "VNSMERLMAB47", "G52NDDN75HR7", "XKN9EJZKEPM7", "S683KLR9EL36", "JNCFG18J6WS9", "JE4XR5KXXVN8", "ULB5NXEQGHD3", "KUJSELLMN7S9", "FKGLTB7MGQ79", "N698C8KRJXJ3", "JHGVEGMV7TE9", "CJVLHBFNLZB8", "KBYAH3LM2NC3", "V2LAJU8XGUA3", "HC5ZSNN1JYU8", "RTRNDGPTMYT9", "HAB2Q9GTNWC3", "YMZRNJSV3J56", "SJ3ZM6FWCVB9", "JRKZRD2M3Q88", "T9QFTSKB4JA4", "DH8BG57LSBN6", "KNF6DKF2TLH2", "F3TGNCN8NGE3", "LSWRJE8Q2TA4", "Z6K9TBPLFWG5", "HN3EDLEMF3P7", "XGB2C9X38TN7", "KMB2SGNQCT51", "EH22VUVXXF36", "VM25SM9D3V38", "FGMTFH5SLZW6", "NRFSNKUCK5R7", "P67FPFGKNZ41", "ND22LZ57VUJ8", "JUPKNDYCG6N9", "J5FEUQGN2AS6", "W65HB2KCMN89", "JW8RKHDL23J5", "TNC1EG2JH871", "VYBZHJKQNPD5", "QN9DY1527L97", "C36JUKF6YKH6", "XNTCEHQKPS68", "HRHAPQDBBME4", "V2KLJJ7GBMV8", "Z6VRKM6JKRH1", "UAHDA1UVFER7", "GHP3ZLXKN2H2", "NN8TQAYEC1E5", "EJD5M37KQBE9", "Z6L1J9BLWSY6", "S6FWTK2R8SC5", "ELKZE6KNQ8N7", "RM29CYH5VV74", "HYBLSJAMM2F4", "PMRAPK4NLQC1", "F1Z2RKRJ2BL2", "HXCKV6FG9YV3", "EN16JU5FMJC3", "ML71MECNK5E7", "J4ELL7L3JCM8", "E1JWF2D5LYS5", "Q2UGLRRQLTW3", "S4FBKXAXVUM5", "UR7TQLQE1D76", "DXU5KP7A3651", "XG5TBDYQJG67", "JP4YVDNXHND5", "RSNBYAMQPE68", "KF7RTKAMXPK5", "E65SM7VSJKL7", "L693MQDFLKD1", "JU9GLKSCUXE3", "GJ3QJ6QD5CX6", "YEKUX9NPDZ77", "PWMKVV55NND4", "MX7ZGEXN9JL6", "UL4CSL529QN5", "TP33LN31J923", "K9CGT3RRVHG3", "TX52W6K8SJM5", "G6GEL7TX2F73", "JMFDD2VBNRK6", "F55TVFUECMB7", "VF29PHJ17649", "MLM8RLDM5C34", "MF72EFWRXD33", "R8UHM5JSEAJ8", "TKV1FZ6WCFF3", "C4F4EWNSMYD8", "CYELYMU4SXK7", "QKZTDK8JXYN4", "S7FRFZTND2N9", "UMDRULGA92G1", "E3ZRDQJ842L5", "HBZCNLDU5QM9", "XG3DMJ6GVQ58", "NKGELFRHPEJ5", "T6VZPTM12MT3", "QA24U4TLPTY6", "R3R9CQY33UA7", "FGV7CGM99H96", "VKVEME15FKA6", "XESNAZL16NV1", "DZTKKRM97YU8", "J776SULJHEE6", "JKCNRN7UP3P2", "K3LEJK8GNYN6", "F6QQBZLNN9E7", "TR28NG75LEZ5", "PCA2QK73LTN3", "LKJQU3YGJ186", "DGYYA5WN7V63", "L2MHJNZNUEA7", "G5JYTL848NJ7", "QPERNAJJAB99", "V5HMGM8JL2X5", "XJSSXCN2YBB8", "WCA2FLYXMB77", "DU7EZMY3CE59", "SNCKMPABPLM3", "X3GGLHL94E74", "RMPMAGMJSKC5", "GAVJPMTUR6N6", "V79GZKJ54KX3", "QAXLQ6QBBKP7", "NL2VTBR2UCM5", "C1H4KXRJP1C5", "MNS4QPJW8TX8", "CLCDBKQ798S2", "Q4JEHU72EEJ8", "ULMPR15NJ766", "NSX5C6L5JHZ6", "P6R6YJ8TYZM6", "V6Y5MMVCJLL5", "KNJQU2KVY525", "G59NFMSCQ9C3", "X11XFHJAC168", "YTW6FCGZNB59", "MQNDLMLN2CR2", "K64MMGPAN1B6", "D92PS15LXM27", "PRGLENJ2D496", "WJ2ADCJB1K84", "TJNNXSWREAR5", "QHZMDMG3VKQ3", "JRM2EB3V1664", "C7JPPSWGNWJ4", "HWBENDLMDMS6", "FGXKVBFFZC99", "WJ33MKGWSLK9", "HCANFVAD1Q33", "Y19HK6NM64E1", "XRYRTMBQV9F1", "Y75ZJ9QZ36P5", "WM2TSMFPP9V3", "CYRFS9AHUJH6", "CBGDLDDH2NM6", "V8R6QY7MXEJ6", "MNYFJL47CCX6", "YSQMHRS4HSC5", "S6NPMLHEH6S1", "JZVDR9JMYBG7", "VM45UTL9JTH1", "RANZPCTJ1RM4", "N7R4MD7D5M89", "KNV8E5VRLHT9", "ZVAPCDXH62J8", "TH8UPX3NCKH4", "VJ3XVZC76HT9"
]


def enrich_prime_awards():
    """
    Enrich the prime awards table with KBR/affiliate flag.
    Adds:
        - kbr_prime: TRUE if uei in UEI_LIST
    """
    start_time = time.time()
    logger.info("Starting enrichment for prime awards...")
    with engine.begin() as connection:
        kbr_uei_list = ', '.join([f"'{x}'" for x in UEI_LIST])
        # kbr_prime: TRUE if recipient_uei in UEI_LIST
        update_kbr_prime = text(f"""
            UPDATE s2_interim.usaspending_prime_awards_dedup
            SET kbr_prime = TRUE
            WHERE recipient_uei IN ({kbr_uei_list})
        """)
        result1 = connection.execute(update_kbr_prime)
        logger.info(f"Updated kbr_prime to TRUE for {result1.rowcount:,} rows.")

        # kbr_as_sub: TRUE if a KBR UEI is a subawardee for this contract and the prime recipient is NOT KBR
        update_kbr_as_sub = text(f"""
            UPDATE s2_interim.usaspending_prime_awards_dedup p
            SET kbr_as_sub = TRUE
            WHERE p.recipient_uei NOT IN ({kbr_uei_list})
              AND EXISTS (
                SELECT 1 FROM s2_interim.usaspending_subawards_dedup s
                WHERE s.prime_award_unique_key = p.contract_award_unique_key
                  AND s.subawardee_uei IN ({kbr_uei_list})
              )
        """)
        result2 = connection.execute(update_kbr_as_sub)
        logger.info(f"Updated kbr_as_sub to TRUE for {result2.rowcount:,} rows.")

        # kbr_sub_issued: TRUE if this contract_award_unique_key ever appears as prime_award_unique_key in any subaward
        update_kbr_sub_issued = text(f"""
            UPDATE s2_interim.usaspending_prime_awards_dedup
            SET kbr_sub_issued = TRUE
            WHERE contract_award_unique_key IN (
                SELECT DISTINCT prime_award_unique_key FROM s2_interim.usaspending_subawards_dedup WHERE prime_award_unique_key IS NOT NULL
            )
        """)
        result3 = connection.execute(update_kbr_sub_issued)
        logger.info(f"Updated kbr_sub_issued to TRUE for {result3.rowcount:,} rows.")

        row_count = connection.execute(text("SELECT COUNT(*) FROM s2_interim.usaspending_prime_awards_dedup")).scalar()
        logger.info(f"Prime awards enrichment complete. Table has {row_count:,} rows.")
    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    logger.info(f"Prime enrichment completed in {minutes}m {seconds}s ({elapsed:.2f} seconds).")
    return row_count

def enrich_subawards():
    """
    Enrich the subawards table by joining to prime awards and adding KBR/affiliate flags.
    Adds:
        - All prime columns (prefixed as needed)
        - kbr_as_sub: TRUE if subawardee_uei in UEI_LIST AND joined prime recipient_uei is NOT in UEI_LIST
        - kbr_sub_issued: TRUE if joined prime uei in UEI_LIST
    """
    start_time = time.time()
    logger.info("Starting enrichment for subawards...")
    # Determine batch size for ~10 batches
    with engine.begin() as connection:
        # Safety: avoid indefinite waits
        try:
            connection.execute(text("SET LOCAL statement_timeout = '30min'"))
        except Exception as _:
            pass
        min_key = connection.execute(text("SELECT MIN(subaward_unique_key) FROM s2_interim.usaspending_subawards_dedup")).scalar()
        max_key = connection.execute(text("SELECT MAX(subaward_unique_key) FROM s2_interim.usaspending_subawards_dedup")).scalar()
    if min_key is None or max_key is None:
        logger.warning("No subaward_unique_key values found. Skipping enrichment.")
        return 0
    total_rows = max_key - min_key + 1
    batch_size = max(1, total_rows // 10)
    logger.info(f"Batch size for subawards enrichment set to {batch_size} to complete in ~10 batches.")
    with engine.begin() as connection:

        # Materialize best prime row per contract_award_unique_key into a temp/interim table
        kbr_uei_list = ', '.join([f"'{x}'" for x in UEI_LIST])
        prime_cols = connection.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = 's2_interim' AND table_name = 'usaspending_prime_awards_dedup'
        """)).fetchall()
        prime_cols = [row[0] for row in prime_cols]
        sub_cols = connection.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = 's2_interim' AND table_name = 'usaspending_subawards_dedup'
        """)).fetchall()
        sub_cols = [row[0] for row in sub_cols]
        join_prime_cols = [col for col in prime_cols if col not in sub_cols or col == 'contract_award_unique_key']
        select_prime_cols = []
        target_prime_cols = []
        for col in join_prime_cols:
            if col == 'contract_award_unique_key':
                select_prime_cols.append(f"prime.{col} AS contract_award_unique_key")
                target_prime_cols.append("contract_award_unique_key")
            else:
                select_prime_cols.append(f"prime.{col} AS prime_{col}")
                target_prime_cols.append(f"prime_{col}")
        kbr_flag_cols = {"kbr_prime", "kbr_as_sub", "kbr_sub_issued"}
        select_sub_cols = [f"s.{col}" for col in sub_cols if col not in kbr_flag_cols]
        target_sub_cols = [col for col in sub_cols if col not in kbr_flag_cols]
        select_cols = select_sub_cols + select_prime_cols
        target_cols = target_sub_cols + target_prime_cols + ["kbr_prime", "kbr_as_sub", "kbr_sub_issued"]
        select_cols_str = ',\n    '.join(select_cols)
        target_cols_str = ', '.join(target_cols)

        # Step 1: Create bestmod TEMP table via batched keys to avoid large sorts/memory spikes
        logger.info("Collecting referenced contract_award_unique_key values into TEMP table...")
        connection.execute(text("DROP TABLE IF EXISTS pg_temp.sub_keys"))
        connection.execute(text(
            """
            CREATE TEMP TABLE sub_keys AS
            SELECT ROW_NUMBER() OVER (ORDER BY prime_award_unique_key) AS rn,
                   prime_award_unique_key AS contract_award_unique_key
            FROM (
                SELECT DISTINCT prime_award_unique_key
                FROM s2_interim.usaspending_subawards_dedup
                WHERE prime_award_unique_key IS NOT NULL
            ) t
            """
        ))
        key_count = connection.execute(text("SELECT COUNT(*) FROM sub_keys")).scalar()
        logger.info(f"Referenced keys collected: {key_count:,}")

        logger.info("Preparing TEMP table prime_awards_bestmod (empty)...")
        connection.execute(text("DROP TABLE IF EXISTS pg_temp.prime_awards_bestmod"))
        connection.execute(text(
            """
            CREATE TEMP TABLE prime_awards_bestmod AS
            SELECT * FROM s2_interim.usaspending_prime_awards_dedup WHERE false
            """
        ))

        keys_per_batch = 50000
        num_key_batches = max(1, (key_count + keys_per_batch - 1) // keys_per_batch)
        logger.info(f"Building bestmod in {num_key_batches} batches of up to {keys_per_batch} keys...")
        total_inserted_best = 0
        t0 = time.time()
        for batch_idx in range(num_key_batches):
            start_rn = batch_idx * keys_per_batch + 1
            end_rn = min((batch_idx + 1) * keys_per_batch, key_count)
            logger.info(f"[Bestmod {batch_idx+1}/{num_key_batches}] Keys rn {start_rn}-{end_rn}...")
            insert_sql = text(
                f"""
                INSERT INTO prime_awards_bestmod
                SELECT DISTINCT ON (p.contract_award_unique_key) p.*
                FROM s2_interim.usaspending_prime_awards_dedup p
                INNER JOIN sub_keys k
                    ON k.contract_award_unique_key = p.contract_award_unique_key
                WHERE k.rn BETWEEN {start_rn} AND {end_rn}
                ORDER BY p.contract_award_unique_key,
                         (p.modification_number = '0') DESC,
                         p.modification_number DESC
                """
            )
            bstart = time.time()
            result = connection.execute(insert_sql)
            bins = result.rowcount if hasattr(result, 'rowcount') else None
            total_inserted_best += (bins or 0)
            logger.info(f"[Bestmod {batch_idx+1}/{num_key_batches}] Inserted {bins if bins is not None else '?'} rows in {time.time()-bstart:.2f}s.")
        logger.info(f"Bestmod TEMP table built with {total_inserted_best:,} rows in {time.time()-t0:.2f}s.")

        # Step 2: Enrich subawards with direct join to bestmod table
        logger.info("Creating subawards_enriched via direct join to TEMP bestmod table...")
        connection.execute(text("DROP TABLE IF EXISTS s2_interim.usaspending_subawards_enriched"))
        create_final_sql = f"""
            CREATE TABLE s2_interim.usaspending_subawards_enriched AS
            SELECT {select_cols_str},
                CASE WHEN prime.recipient_uei IN ({kbr_uei_list}) THEN TRUE ELSE FALSE END AS kbr_prime,
                CASE WHEN s.subawardee_uei IN ({kbr_uei_list}) AND (prime.recipient_uei IS NULL OR prime.recipient_uei NOT IN ({kbr_uei_list})) THEN TRUE ELSE FALSE END AS kbr_as_sub,
                CASE WHEN prime.recipient_uei IN ({kbr_uei_list}) AND (s.subawardee_uei IS NULL OR s.subawardee_uei NOT IN ({kbr_uei_list})) THEN TRUE ELSE FALSE END AS kbr_sub_issued
            FROM s2_interim.usaspending_subawards_dedup s
            LEFT JOIN prime_awards_bestmod prime
                ON s.prime_award_unique_key = prime.contract_award_unique_key
        """
        t1 = time.time()
        connection.execute(text(create_final_sql))
        row_count = connection.execute(text("SELECT COUNT(*) FROM s2_interim.usaspending_subawards_enriched")).scalar()
        logger.info(f"Subawards enriched table created with {row_count:,} rows in {time.time() - t1:.2f}s.")

    elapsed = time.time() - start_time
    minutes = int(elapsed // 60)
    seconds = int(elapsed % 60)
    logger.info(f"Subawards enrichment completed in {minutes}m {seconds}s ({elapsed:.2f} seconds).")
    return row_count

def enrich_all():
    """
    Enrich both prime awards and subawards tables.
    """
    logger.info("Starting enrichment for all tables...")
    start_all = time.time()
    results = {}
    results['prime_awards'] = enrich_prime_awards()
    results['subawards'] = enrich_subawards()
    # Verification step: compare kbr_as_sub and kbr_sub_issued counts
    with engine.begin() as connection:
        kbr_as_sub_prime = connection.execute(text("""
            SELECT COUNT(*) FROM s2_interim.usaspending_prime_awards_dedup WHERE kbr_as_sub IS TRUE
        """)).scalar()
        kbr_as_sub_sub = connection.execute(text("""
            SELECT COUNT(*) FROM s2_interim.usaspending_subawards_enriched WHERE kbr_as_sub IS TRUE
        """)).scalar()
        kbr_sub_issued_prime = connection.execute(text("""
            SELECT COUNT(*) FROM s2_interim.usaspending_prime_awards_dedup WHERE kbr_sub_issued IS TRUE
        """)).scalar()
        kbr_sub_issued_sub = connection.execute(text("""
            SELECT COUNT(*) FROM s2_interim.usaspending_subawards_enriched WHERE kbr_sub_issued IS TRUE
        """)).scalar()
        logger.info(f"Verification: kbr_as_sub (prime table): {kbr_as_sub_prime:,}")
        logger.info(f"Verification: kbr_as_sub (subawards table): {kbr_as_sub_sub:,}")
        logger.info(f"Verification: kbr_sub_issued (prime table): {kbr_sub_issued_prime:,}")
        logger.info(f"Verification: kbr_sub_issued (subawards table): {kbr_sub_issued_sub:,}")
        if kbr_as_sub_prime != kbr_as_sub_sub:
            logger.warning(f"Mismatch: kbr_as_sub count differs between prime ({kbr_as_sub_prime:,}) and subawards ({kbr_as_sub_sub:,}) tables!")
        else:
            logger.info("kbr_as_sub counts match between prime and subawards tables.")
        if kbr_sub_issued_prime != kbr_sub_issued_sub:
            logger.warning(f"Mismatch: kbr_sub_issued count differs between prime ({kbr_sub_issued_prime:,}) and subawards ({kbr_sub_issued_sub:,}) tables!")
        else:
            logger.info("kbr_sub_issued counts match between prime and subawards tables.")
    elapsed_all = time.time() - start_all
    minutes_all = int(elapsed_all // 60)
    seconds_all = int(elapsed_all % 60)
    logger.info(f"All enrichment complete in {minutes_all}m {seconds_all}s ({elapsed_all:.2f} seconds).")
    return results

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logger.info(f"Python version: {sys.version}")
    logger.info("Step 2: Enriching deduplicated tables...")
    enrich_all()
