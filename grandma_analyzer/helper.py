import pandas as pd

def calculate_numbers_percent(string):
    digit_count = sum(char.isdigit() for char in string)
    total_characters = len(string)
    return (digit_count / total_characters) * 100

df = pd.read_csv('urls.csv')
# Apply the function to create the 'numbers_percent' column
df['numbers_percent'] = df['url'].apply(lambda x: calculate_numbers_percent(x))

df.drop_duplicates(subset=['url'], inplace=True, keep='first')
# Save the dataframe to a CSV file
df.to_csv('urls_new.csv', index=False)