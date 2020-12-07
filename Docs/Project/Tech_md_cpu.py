from datetime import timedelta
import re
import json
from pandas import DataFrame
from numpy import mean
import mysql.connector

conn_args = { "host" : "localhost",
                "port" : 3306,
                "user" : "root",
                "password" : "password",
                "database" : "anompy", }

trdate = 20191231 # TODO Change to 20200630

with mysql.connector.connect(**conn_args) as conn:
    with conn.cursor() as cursor:

        # Get # of entities
        cmd_select = f"select count(distinct BKCODE) from STATUS where TRDATE={trdate}"
        cursor.execute(cmd_select)
        for result in cursor:
            entities_ct = result[0]
            break
        print("(A)", entities_ct)

        #------------------------------------------------------------------#
        # Compute for (B)

        # Get entities with complete runs (all riids have been processed)
        collect = list()
        cmd_select = f"""
                    select t1.bkcode, t1.riid_ct, t2.riid_done from
                        (select bkcode, count(riidx) as riid_ct from status where TRDATE={trdate} group by bkcode) t1
                            inner join
                        (select bkcode, count(riidx) as riid_done from status
                            where TRDATE={trdate} and isprocessed=1 and not (model is NULL or trim(model) = '')
                            group by bkcode) t2
                                on t1.bkcode = t2.bkcode
                     """
        cursor.execute(cmd_select)
        for result in cursor:
            collect.append({ "BKCODE" : result[0],
                             "RIID_CT" : result[1],
                             "RIID_DONE" : result[2] })
        entities_runp = DataFrame(collect)
        entities_runp.set_index("BKCODE", drop=True, inplace=True)
        # print(entities_runp)

        # Get entities where all RIIDs are done
        entities_done = list(entities_runp[entities_runp["RIID_CT"] == entities_runp["RIID_DONE"]].index)
        # print(entities_done)
        bkcode_list = ", ".join([str(x) for x in entities_done])

        # Get # of riids per bkcode that needed processing
        collect = list()
        cmd_select = f"""
                    select bkcode, count(bkcode) as RIID_COMP from status
                        where TRDATE={trdate} and bkcode in ({bkcode_list}) and
                            model like "%'class':%"
                        group by bkcode
                     """
        cursor.execute(cmd_select)
        for result in cursor:
            collect.append({ "BKCODE" : result[0],
                             "RIID_COMP" : result[1] })
        entities_comp = DataFrame(collect)
        entities_comp.set_index("BKCODE", drop=True, inplace=True)
        # print(entities_comp)

        #
        entities_runp = entities_runp.join(entities_comp)
        entities_runp["RATIO"] = entities_runp["RIID_COMP"] / entities_runp["RIID_CT"]
        #print(entities_runp)

        average_riids_per_entity = mean(entities_runp["RATIO"]) * mean(entities_runp["RIID_CT"])
        print("(B)", average_riids_per_entity)

        #------------------------------------------------------------------#
        # Compute for (C)

        collect = list()
        cmd_select = f"""
                    select model from status
                        where TRDATE={trdate} and bkcode in ({bkcode_list}) and
                            model like "%'class':%'ml_elapsed':%"
                     """
        cursor.execute(cmd_select)
        for result in cursor:
            collect.append({ "MODEL" : result[0] })

        collect_elapsed = list()
        for d in collect:
            model = d["MODEL"]
            md = json.loads(model.replace("'",'"'))
            if "ml_elapsed" in md:
                elapsed_str = md["ml_elapsed"]
                # print(elapsed_str)

                # From https://stackoverflow.com/a/21074460
                def parse(s):
                    if 'day' in s:
                        m = re.match(r'(?P<days>[-\d]+) day[s]*, (?P<hours>\d+):(?P<minutes>\d+):(?P<seconds>\d[\.\d+]*)', s)
                    else:
                        m = re.match(r'(?P<hours>\d+):(?P<minutes>\d+):(?P<seconds>\d[\.\d+]*)', s)
                    _ = {key: float(val) for key, val in m.groupdict().items()}
                    return timedelta(**_)

                ml_elapsed = parse(elapsed_str)
                # print(ml_elapsed)

                collect_elapsed.append(ml_elapsed)

        # Average elapsed
        average_elapsed = mean(collect_elapsed)
        print("(C)", average_elapsed)

        #------------------------------------------------------------------#
        # Compute for (D)

        est_total_run_time = (entities_ct * average_riids_per_entity) * average_elapsed
        print("(D)", str(est_total_run_time))

        #------------------------------------------------------------------#
        # Compute for (E)

        n_child = 3
        print("(E)", str(est_total_run_time / n_child))

