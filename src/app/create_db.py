import os
import pickle
import sqlite3

#create data sources
def create_data_files():
        if not os.path.exists("/src/database/"):
                os.mkdir("/src/database/")
        if not os.path.exists("/src/database/mylog.log"):
                with open("/src/database/mylog.log", "w"):
                        pass

        if not os.path.exists("/src/database/USER_DICT.pkl"):
                with open("/src/database/USER_DICT.pkl", "wb") as f:
                        pickle.dump({'496885396':{'views':set(),"keys":set(['пож','спас','огне']),'price':5000000}}  , f)
                        f.close()
                


        DB_PATH = "/src/database/main.db"
        conn = sqlite3.connect(DB_PATH) 
        c = conn.cursor()

        c.execute('''
                CREATE TABLE IF NOT EXISTS goszakup_lots (
                id TEXT,
                name_short TEXT,
                name_full TEXT,
                qty REAL,
                price REAL,
                lot_type TEXT,
                status TEXT,
                created_date TIMESTAMP);
                ''')
        conn.commit()
      
        c.execute('''
                CREATE TABLE IF NOT EXISTS samruk_lots (
                id TEXT,
                type TEXT,
                name_full TEXT,
                exp_date INT,
                price REAL,
                created_date TIMESTAMP);
                ''')
                        
        conn.commit()
        print(' sqlite3 DB was Created')
