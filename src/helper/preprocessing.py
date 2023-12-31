import pandas as pd
import re
import string
import nltk
# Note: you might need to download the nltk packages
# nltk.download('punkt')
# nltk.download('stopwords')
# nltk.download('wordnet')
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from tqdm import tqdm

from src.helper.utils import load_data, is_english
from src.helper.logger import working_on


def remove_words_with_numbers(word_list):
  """
  Takes a string representation of a list of words as input,
  removes any special characters from the words, and then removes any words that contain numbers.

  Args:
    word_list_str: A string representation of a list of words.

  Returns:
    The function `remove_words_with_numbers` returns a list of words without any special characters or
  numbers.
  """
  word_list_without_special = [
      re.sub(r"[^a-zA-Z0-9\s]", "", word) for word in word_list
  ]
  word_list_without_numbers = [
      word for word in word_list_without_special if not re.search(r"\d", word)
  ]
  return word_list_without_numbers


def convert_date_posted(date_str, date_scraped):
  try:
    days_ago = int(date_str.split(' ')[0])
    actual_date = pd.to_datetime(date_scraped) - pd.Timedelta(days=days_ago)
    return actual_date
  except:
    return date_scraped  # If the format is not "x days ago", use the scraped date


def split_combined_words(text):
  """
  Since during the scraping, some words are combined, e.g. "requirementsYou're" or "offerings.If" we need to split them
  Splits words at:
  1. Punctuation marks followed by capital letters.
  2. Lowercase letters followed by uppercase letters.
  """
  # 1. split
  text = re.sub(r'([!?,.;:])([A-Z])', r'\1 \2', text)

  # 2. split
  text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)

  return text


def text_preprocessing(text):
  """
  Preprocesses text by:
    - Splitting combined words
    - Tokenizing
    - Removing stopwords
    - Remove punctuation
    - Lemmatizing
  """

  text = split_combined_words(text)
  text = text.lower()

  # Remove punctuation
  text = re.sub(f'[{string.punctuation}]', '', text)
  # Remove numbers
  text = re.sub(r'\d+', '', text)

  tokens = word_tokenize(text)

  stop_words = set(stopwords.words('english'))

  lemmatizer = WordNetLemmatizer()
  tokens = [lemmatizer.lemmatize(w) for w in tokens if w not in stop_words]

  punctuation = {'!', ',', '.', ';', ':', '?',
                 '(', ')', '[', ']', '-', '+', '"', '*', '—', '•', '’', '‘', '“', '”', '``'}
  tokens = [w for w in tokens if w not in punctuation]

  # Remove last 3 words since they are always the same (scraped buttons from the website)
  tokens = tokens[:-3]

  return tokens


def preprocess():
  """
  Main function of the preprocessing module.
  Loads the raw data and does the following:
  - Checks for english language
  - Removes rows with missing descriptions
  - Inferes the date posted
  - Preprocesses the description
  - Saves the preprocessed data to data/processed/cleaned_jobs.csv
  """

  working_on("Loading data")
  df = load_data(kind="raw")

  # Remove duplicates
  df.drop_duplicates(subset=['id'], inplace=True)
  df.drop_duplicates(subset=['description'], inplace=True)
  # Filter out jobs with missing descriptions
  df = df[df['description'].notna()]

  working_on("Filtering out non-english descriptions ...")
  for index, row in df.iterrows():
    if not is_english(row['description'][:100]):
      df.drop(index, inplace=True)

  working_on("Infering dates ...")
  df['date_posted'] = df.apply(lambda x: convert_date_posted(
      x['date_posted'], x['date_scraped']), axis=1)

  # Lower case all text
  df['title'] = df['title'].str.lower()
  df['function'] = df['function'].str.lower()
  df['industries'] = df['industries'].str.lower()
  df['industries'] = df['industries'].str.replace('\n', ' ')

  # Removing outliers (where industries is whole description of offer)
  df["industries_length"] = df["industries"].str.split()
  df["industries_length"] = df["industries_length"].str.len()
  df = df[df["industries_length"] < 15]
  df.drop(columns=["industries_length"], inplace=True)

  df["industries"] = df["industries"].str.replace(" and ", ",")
  df["function"] = df["function"].str.replace(" and ", ",")
  df["industries"] = df["industries"].str.replace("/", ",")
  df["function"] = df["function"].str.replace("/", ",")

  df["industries"] = df["industries"].str.replace(r",,|, ,", ",")
  df["function"] = df["function"].str.replace(r",,|, ,", ",")

  tqdm.pandas(desc="🐼 Preprocessing description", ascii=True, colour="#0077B5")

  df['description'] = df['description'].progress_apply(text_preprocessing)

  # Remove rows with empty descriptions or descriptions containing less than 3 words
  df = df[df['description'].map(len) > 3]

  # Remove special characters and numbers from the tokenized list
  df['description'] = df['description'].apply(
      lambda x: remove_words_with_numbers(x)
  )

  df = df.reset_index(drop=True)

  working_on("Saving preprocessed data ...")
  df.to_csv('data/processed/cleaned_jobs.csv', index=False, sep=';')


if __name__ == "__main__":
  preprocess()
  df = load_data(kind="processed")
  print(df.iloc[970]['description'])
  print(df.iloc[970]['industries'])
  # print(df.iloc[970]['function'])
  print(df.head())
  print(df)
