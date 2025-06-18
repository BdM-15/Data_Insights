# usaspending_subawards_kbr_issued_from_db.py
"""
Creates s3_processed.usaspending_subawards_kbr_issued by joining all KBR prime awards (from s3_processed.usaspending_prime_awards, filtered by UEI list)
with all subawards (from s3_processed.usaspending_subawards) on contract_award_unique_key = prime_award_unique_key.

- Filters prime awards by recipient_uei or recipient_parent_uei (from provided UEI list)
- Joins to subawards on contract_award_unique_key = prime_award_unique_key
- Preserves all subaward columns, and adds prime award context (recipient_parent_name, recipient_name, award_id_piid, naics_code, etc.)
- Drops and recreates the destination table on each run
- Follows Data_Insights project standards
"""
import os
import sys
import logging
from typing import List
import psycopg2
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
import config

# --- Logging Setup ---
def setup_logging(log_file: str = 'logs/usaspending_subawards_kbr_issued_db.log'):
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    logger = logging.getLogger("usaspending_subawards_kbr_issued_db")
    logger.setLevel(logging.INFO)
    if logger.handlers:
        logger.handlers.clear()
    file_handler = logging.FileHandler(log_file)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False
    return logger

logger = setup_logging()

# --- UEI List ---
UEI_LIST = [
    "XHHKVBDUP7R7", "SJ3QANR912G1", "JLSPHGZAF8L6", "S2MGFVL4HBL5", "WE11DMUYFR78", "LQGKFHF5GPX3", "W62YK6JFBJ28", "X4Z6XB7P2B95", "TWGDVBNK8LS7", "SCAHJH4FK963", "QRFKN8FEW498", "KJMYKBBNPU43", "ZM5WSGWLU463", "CKWAM5SJ3LK9", "ME4QS8H2KVX3", "GVLUCB2UX283", "JWK8UZM4WL51", "XNYZKKKJS698", "H7AJRBSDAAB3", "MAWLPJ3BGGL6", "FYDWBRMLRJM7", "C1F3PCZ648T3", "M6MUL8P5GNR7", "FPH1KB2KZSZ8", "KVC9Z1B19AY5", "KPVDRF17NW72", "UCF2ZAF3TD81", "CAEVQ5LJDJ43", "QWBYGNFNT4T6", "UF7GLXU2DEH5", "VKF1DSWRNK27", "TAG1WEXVRLT1", "F6G4L8SJ2UW3", "LCACMNJ44LA5", "TGQRD3UGFPR9", "V3M7LMQMXWT3", "G9HUM7929KT7", "ZUZ5MU8W2EK2", "H4JZA4SFLJT1", "NN4ARC7E4SP7", "C158H578Y149", "MG76VDBB7HT8", "RYDLKTFHJNE1", "FV9WW8AP1NB3", "NHMQSLZ6DFB9", "Y32CU9FBJDR8", "PULAGF1NFNY1", "VNSMERLMAB47", "G52NDDN75HR7", "XKN9EJZKEPM7", "S683KLR9EL36", "JNCFG18J6WS9", "JE4XR5KXXVN8", "ULB5NXEQGHD3", "KUJSELLMN7S9", "FKGLTB7MGQ79", "N698C8KRJXJ3", "JHGVEGMV7TE9", "CJVLHBFNLZB8", "KBYAH3LM2NC3", "V2LAJU8XGUA3", "HC5ZSNN1JYU8", "RTRNDGPTMYT9", "HAB2Q9GTNWC3", "YMZRNJSV3J56", "SJ3ZM6FWCVB9", "JRKZRD2M3Q88", "T9QFTSKB4JA4", "DH8BG57LSBN6", "KNF6DKF2TLH2", "F3TGNCN8NGE3", "LSWRJE8Q2TA4", "Z6K9TBPLFWG5", "HN3EDLEMF3P7", "XGB2C9X38TN7", "KMB2SGNQCT51", "EH22VUVXXF36", "VM25SM9D3V38", "FGMTFH5SLZW6", "NRFSNKUCK5R7", "P67FPFGKNZ41", "ND22LZ57VUJ8", "JUPKNDYCG6N9", "J5FEUQGN2AS6", "W65HB2KCMN89", "JW8RKHDL23J5", "TNC1EG2JH871", "VYBZHJKQNPD5", "QN9DY1527L97", "C36JUKF6YKH6", "XNTCEHQKPS68", "HRHAPQDBBME4", "V2KLJJ7GBMV8", "Z6VRKM6JKRH1", "UAHDA1UVFER7", "GHP3ZLXKN2H2", "NN8TQAYEC1E5", "EJD5M37KQBE9", "Z6L1J9BLWSY6", "S6FWTK2R8SC5", "ELKZE6KNQ8N7", "RM29CYH5VV74", "HYBLSJAMM2F4", "PMRAPK4NLQC1", "F1Z2RKRJ2BL2", "HXCKV6FG9YV3", "EN16JU5FMJC3", "ML71MECNK5E7", "J4ELL7L3JCM8", "E1JWF2D5LYS5", "Q2UGLRRQLTW3", "S4FBKXAXVUM5", "UR7TQLQE1D76", "DXU5KP7A3651", "XG5TBDYQJG67", "JP4YVDNXHND5", "RSNBYAMQPE68", "KF7RTKAMXPK5", "E65SM7VSJKL7", "L693MQDFLKD1", "JU9GLKSCUXE3", "GJ3QJ6QD5CX6", "YEKUX9NPDZ77", "PWMKVV55NND4", "MX7ZGEXN9JL6", "UL4CSL529QN5", "TP33LN31J923", "K9CGT3RRVHG3", "TX52W6K8SJM5", "G6GEL7TX2F73", "JMFDD2VBNRK6", "F55TVFUECMB7", "VF29PHJ17649", "MLM8RLDM5C34", "MF72EFWRXD33", "R8UHM5JSEAJ8", "TKV1FZ6WCFF3", "C4F4EWNSMYD8", "CYELYMU4SXK7", "QKZTDK8JXYN4", "S7FRFZTND2N9", "UMDRULGA92G1", "E3ZRDQJ842L5", "HBZCNLDU5QM9", "XG3DMJ6GVQ58", "NKGELFRHPEJ5", "T6VZPTM12MT3", "QA24U4TLPTY6", "R3R9CQY33UA7", "FGV7CGM99H96", "VKVEME15FKA6", "XESNAZL16NV1", "DZTKKRM97YU8", "J776SULJHEE6", "JKCNRN7UP3P2", "K3LEJK8GNYN6", "F6QQBZLNN9E7", "TR28NG75LEZ5", "PCA2QK73LTN3", "LKJQU3YGJ186", "DGYYA5WN7V63", "L2MHJNZNUEA7", "G5JYTL848NJ7", "QPERNAJJAB99", "V5HMGM8JL2X5", "XJSSXCN2YBB8", "WCA2FLYXMB77", "DU7EZMY3CE59", "SNCKMPABPLM3", "X3GGLHL94E74", "RMPMAGMJSKC5", "GAVJPMTUR6N6", "V79GZKJ54KX3", "QAXLQ6QBBKP7", "NL2VTBR2UCM5", "C1H4KXRJP1C5", "MNS4QPJW8TX8", "CLCDBKQ798S2", "Q4JEHU72EEJ8", "ULMPR15NJ766", "NSX5C6L5JHZ6", "P6R6YJ8TYZM6", "V6Y5MMVCJLL5", "KNJQU2KVY525", "G59NFMSCQ9C3", "X11XFHJAC168", "YTW6FCGZNB59", "MQNDLMLN2CR2", "K64MMGPAN1B6", "D92PS15LXM27", "PRGLENJ2D496", "WJ2ADCJB1K84", "TJNNXSWREAR5", "QHZMDMG3VKQ3", "JRM2EB3V1664", "C7JPPSWGNWJ4", "HWBENDLMDMS6", "FGXKVBFFZC99", "WJ33MKGWSLK9", "HCANFVAD1Q33", "Y19HK6NM64E1", "XRYRTMBQV9F1", "Y75ZJ9QZ36P5", "WM2TSMFPP9V3", "CYRFS9AHUJH6", "CBGDLDDH2NM6", "V8R6QY7MXEJ6", "MNYFJL47CCX6", "YSQMHRS4HSC5", "S6NPMLHEH6S1", "JZVDR9JMYBG7", "VM45UTL9JTH1", "RANZPCTJ1RM4", "N7R4MD7D5M89", "KNV8E5VRLHT9", "ZVAPCDXH62J8", "TH8UPX3NCKH4", "VJ3XVZC76HT9"
]

def main():
    logger.info("Connecting to PostgreSQL database...")
    conn = psycopg2.connect(
        host=config.PG_HOST,
        port=config.PG_PORT,
        dbname=config.PG_DATABASE,
        user=config.PG_USER,
        password=config.PG_PASSWORD
    )
    cursor = conn.cursor()
    # Get all columns from subawards
    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = 's3_processed' AND table_name = 'usaspending_subawards' ORDER BY ordinal_position;")
    subaward_columns = [row[0] for row in cursor.fetchall()]
    subaward_col_str = ', '.join([f'"sub"."{col}"' for col in subaward_columns])
    # Get selected columns from prime awards for context
    prime_context_cols = [
        'recipient_parent_name', 'recipient_name', 'award_id_piid', 'naics_code', 'naics_description',
        'product_or_service_code', 'product_or_service_code_description', 'parent_award_agency_name',
        'funding_agency_name', 'funding_sub_agency_name', 'funding_office_name', 'contract_award_unique_key'
    ]
    prime_col_str = ', '.join([f'pa."{col}"' for col in prime_context_cols])
    # Drop destination table if it exists
    logger.info("Dropping destination table if it exists...")
    cursor.execute("DROP TABLE IF EXISTS s3_processed.usaspending_subawards_kbr_issued;")
    conn.commit()
    # Create destination table with all subaward columns + selected prime context columns
    create_cols = ',\n    '.join([f'"{col}" text' for col in subaward_columns] + [f'"{col}" text' for col in prime_context_cols])
    cursor.execute(f"""
        CREATE TABLE s3_processed.usaspending_subawards_kbr_issued (
            {create_cols}
        );
    """)
    conn.commit()
    # Build join and filter logic with deduplication
    logger.info("Joining KBR prime awards to subawards and inserting into destination table with deduplication...")
    sql_uei = ','.join(['%s'] * len(UEI_LIST))
    # Determine deduplication key
    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = 's3_processed' AND table_name = 'usaspending_subawards' ORDER BY ordinal_position;")
    subaward_columns = [row[0] for row in cursor.fetchall()]
    if 'subaward_id' in subaward_columns:
        distinct_on = 'sub.subaward_id'
    else:
        distinct_on = 'sub.prime_award_unique_key, sub.subaward_number, sub.subaward_action_date'
    subaward_col_str = ', '.join([f'sub."{col}"' for col in subaward_columns])
    prime_col_str = ', '.join([f'pa."{col}"' for col in prime_context_cols])
    join_query = f"""
        SELECT DISTINCT ON ({distinct_on}) {subaward_col_str}, {prime_col_str}
        FROM s3_processed.usaspending_prime_awards pa
        INNER JOIN s3_processed.usaspending_subawards sub
            ON pa.contract_award_unique_key = sub.prime_award_unique_key
        WHERE pa.recipient_uei IN ({sql_uei}) OR pa.recipient_parent_uei IN ({sql_uei})
        ORDER BY {distinct_on}
    """
    cursor.execute(join_query, UEI_LIST + UEI_LIST)
    rows = cursor.fetchall()
    logger.info(f"Fetched {len(rows)} subawards issued by KBR primes.")
    # Insert into destination table
    if rows:
        insert_cols = ', '.join([f'"{col}"' for col in subaward_columns + prime_context_cols])
        insert_query = f"INSERT INTO s3_processed.usaspending_subawards_kbr_issued ({insert_cols}) VALUES ({','.join(['%s']*len(subaward_columns + prime_context_cols))})"
        for row in tqdm(rows, desc="Inserting records"):
            cursor.execute(insert_query, row)
        conn.commit()
        logger.info(f"Inserted {len(rows)} records into s3_processed.usaspending_subawards_kbr_issued.")
    else:
        logger.info("No records to insert.")
    cursor.close()
    conn.close()
    logger.info("Done.")

if __name__ == "__main__":
    main()
