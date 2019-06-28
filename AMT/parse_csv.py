import csv
import string

hit_csv = csv.reader(open('HIT_RESULTS.csv', 'r'), delimiter = ',') 

sec_pred_csv = csv.writer(open('SECOND_PRED_RESULTS.csv', 'w'), delimiter = ',')
sec_pred_csv.writerow(["HIT ID","HOSPITAL","ASSIGNMENT ID","TIME TAKEN","WORKER VOTE"])

unparseable_sec_pred_csv = csv.writer(open('UNPARSEABLE_SECOND_PRED_RESULTS.csv', 'w'), delimiter = ',')
unparseable_sec_pred_csv.writerow(["HIT ID","HOSPITAL","ASSIGNMENT ID","TIME TAKEN","WORKER VOTE"])

joinable_filter_csv = csv.writer(open('JOINABLE_FILTER_RESULTS.csv', 'w'), delimiter = ',')
joinable_filter_csv.writerow(["HIT ID","HOTEL","ASSIGNMENT ID","TIME TAKEN","WORKER VOTE"])
for assignment in hit_csv:
    if assignment[4] == "( eval_secondary_pred)":
        answer = assignment[8]
        if answer[0].isdigit():
            for i in range(len(answer)):
                if not answer[i].isdigit():
                    answer = answer[:i+1]
                    break
            if int(answer) < 5:
                answer = "less than 5"
            else:
                answer = "greater than or equal to 5"
            sec_pred_csv.writerow([assignment[0],assignment[3],assignment[5],assignment[7],answer])

        else:
            unparseable_sec_pred_csv.writerow([assignment[0],assignment[3],assignment[5],assignment[7],answer])

    elif assignment[4] == "( eval_joinable_filter)":
        joinable_filter_csv.writerow([assignment[0],assignment[2],assignment[5],assignment[7],assignment[8]])




