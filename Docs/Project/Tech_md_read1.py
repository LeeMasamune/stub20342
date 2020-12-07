#

BKCODE=50
ACCT="105050000000000000"
SCHNO="00"
BOOK=0
REPORT="FRPSSOCSIE"
AMTCOL="TOTAMT"

################################################################################

from datetime import datetime
from pandas import DataFrame

################################################################################

def run_sequential():
    """Get historical data from multiple *.sas7bdat files
    """

    from pathlib import Path
    from pandas import read_sas

    collect = DataFrame()

    # Directory containing *.SAS7BDAT
    in_dir = r"\\fileserver_prd\SDC_SASWORK\NEWFRP" # r"D:\repos\synth\gen1\NEWFRP"

    # It must be known beforehand that the BKCODE only exists in
    #   KBSSOCSIE_* files so we don't run other files needlessly
    pathlist = Path(in_dir).rglob("KBSSOCSIE_*.sas7bdat") # This is case sensitive on *NIX
    for path in pathlist:
        # because path is object not string
        path_str = str(path)
        print("reading", path_str)
        in_df = read_sas(path_str)

        # Decode b'xxx' strings
        in_df["SCHNO"] = in_df["SCHNO"].apply(lambda x: x.decode("utf-8"))
        in_df["ACCT"] = in_df["ACCT"].apply(lambda x: x.decode("utf-8"))

        # Filter data
        select_df = (in_df["BKCODE"] == BKCODE) & (in_df["ACCT"] == ACCT) & (in_df["SCHNO"] == SCHNO) & (in_df["BOOK"] == BOOK)
        row_df = in_df[select_df]
        row_df.reset_index(inplace=True)
        collect = collect.append(row_df[["TRDATE", "TOTAMT"]], ignore_index=True)
        collect.reset_index(drop=True, inplace=True)

    print(collect) # Data is now usable somewhere else

################################################################################

def run_indexed():
    """Get historical data from MySQL server
    """

    import mysql.connector

    conn_args = { "host" : "localhost",
                  "port" : 3306,
                  "user" : "user",
                  "password" : "password",
                  "database" : "anompy", }

    collect = list()

    with mysql.connector.connect(**conn_args) as conn:
        with conn.cursor() as cursor:
            # SQL query
            cursor.execute(f"""
                select trdate, value from raw
                    where BKCODE={BKCODE} and
                        riidx in
                            (
                                select idx from riid where
                                    report='{REPORT}' and
                                    schno='{SCHNO}' and
                                    book={BOOK} and
                                    acct='{ACCT}' and
                                    amtcol='{AMTCOL}'
                            )
                            """)

            for result in cursor:
                collect.append({ "TRDATE" : result[0], "VALUE" : result[1] })

    # Load collected data to DataFrame
    df = DataFrame(collect)
    print(df) # Data is now usable somewhere else

################################################################################

# Benchmark sequential
start = datetime.now()
run_sequential()
end = datetime.now()
s_elapsed = end - start
print("SEQUENTIAL: ", s_elapsed)

# Benchmark indexed
start = datetime.now()
run_indexed()
end = datetime.now()
i_elapsed = end - start
print("INDEXED: ", i_elapsed)

print("-" * 80)
print("SEQUENTIAL: ", s_elapsed)
print("INDEXED: ", i_elapsed)
