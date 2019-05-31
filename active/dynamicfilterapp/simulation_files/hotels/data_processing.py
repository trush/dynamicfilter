# import numpy as np

# new_f = open('Hotel_times.csv', 'w')
# f = open('Hotel_cleaned_data.csv', 'rb')

# pred = None
# times = ''

# answers = np.genfromtxt(fname = 'Hotel_cleaned_data.csv', dtype = str, delimiter = ",")
# for line in answers:
#     cur_pred = line[2]
#     if pred is None or pred =='Input.Question':
#         pred = cur_pred
#     if not pred == cur_pred:
#         times = times.rstrip(',')
#         new_f.write(times+'\n')
#         pred=cur_pred
#         times = ''
#     if not pred == 'Input.Question':
#         times += line[0] + ','
    
f = open('Hotel_questions.csv', 'r')
times = open('Hotel_times.csv', 'r')
time_array = []
for time in times:
    time_array += [time]
index=0
for line in f:
    line = line.rstrip('\n')
    time_taken = time_array[index].rstrip('\n')
    print line
    print time_taken
f.close()
times.close()

 