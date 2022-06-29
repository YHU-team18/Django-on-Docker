import os
import json
from math import log

import PyPDF2
# 初回のみ必要
if not os.path.isdir('/root/nltk_data/corpora/wordnet'): # データが存在しない場合ダウンロードする
    import nltk
    nltk.download('wordnet')
    nltk.download('stopwords')
    nltk.download('omw-1.4')
from nltk.stem.wordnet import WordNetLemmatizer as WNL
from nltk.corpus import stopwords

wnl = WNL()
stop_words = stopwords.words('english')

# 単語頻度データの読み込み
base_path = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.normpath(os.path.join(base_path, '../PDFtoBoW/words_by_frequency.txt'))
with open(file_path, 'r') as f:
    words = f.read().split()

# 英和辞典データの読み込み
ejdict_path = os.path.normpath(os.path.join(base_path, '../PDFtoBoW/ejdict_all.json'))
with open(ejdict_path, 'r') as f:
    ejdict = json.load(f)

wordcost = dict((k, log((i+1)*log(len(words)))) for i,k in enumerate(words))
maxword = max(len(x) for x in words)

def infer_spaces(s):
    """スペースの入っていない未分割の単語文字列に対してスペースの位置を推測する
        Wikipediaの単語頻度データを利用: https://github.com/IlyaSemenov/wikipedia-word-frequency
    Args:
        s (_str_): 未分割の単語文字列
    Returns:
        _str_ : スペースによって分割された単語を含む文字列
    """
    def best_match(i): # Returns a pair of (match_cost, match_length)
        candidates = enumerate(reversed(cost[max(0, i-maxword):i]))
        return min((c + wordcost.get(s[i-k-1:i], 9e999), k+1) for k,c in candidates)

    # コストのリスト
    cost = [0]
    for i in range(1,len(s)+1):
        c,k = best_match(i)
        cost.append(c)

    # コストの最も低くなる分割を探す
    output = []
    i = len(s)
    while i>0:
        c,k = best_match(i)
        assert c == cost[i]
        output.append(s[i-k:i])
        i -= k

    return " ".join(reversed(output))

def lemmatization(file_dir):
    """PDFファイルのパスを受け取り,レマ化した単語のリストを返す
    Args:
        file_dir (_str_): PDFファイルのパス

    Returns:
        _list_: レマ化された英単語文字列(_str_)のリスト
    """
    with open(file_dir, 'rb') as f:
        lemmatized_words = []
        reader = PyPDF2.PdfFileReader(f)
        # 各ページごとに文字列を単語へ分割後,レマ化を行いリストへ保存
        for i in range(reader.getNumPages()):
            page = reader.getPage(i)
            raw_text = page.extractText()
        # 改行部分の処理としてハイフンと改行文字の除去を行う
            bar = raw_text.translate(str.maketrans({'-': None, '\n': None}))
            for i in bar.split():
            # スペースで分割できなかった単語に対しての分割を行う
                candidate_words = infer_spaces(i).split()
                for word in candidate_words:
                    lemmatized_words.append(wnl.lemmatize(word))
    return lemmatized_words

def get_BoW(file_dir):
    """PDFファイルのパスを受け取り,{'英単語': 出現頻度}のdictを返す
    Args:
        file_dir (_str_): PDFファイルのパス

    Returns: 
        _dict_: 英単語がkey,PDFファイル内での出現頻度がvalueになったdict
    """
    BoW_frequency = {}
    lemmatized_words = lemmatization(file_dir)
    for lemmatized_word in lemmatized_words:
        if (lemmatized_word not in stop_words) and (len(lemmatized_word) > 1):
        # BoW_frequency: {'単語': 頻度}の辞書
            BoW_frequency.setdefault(lemmatized_word, 0)
            BoW_frequency[lemmatized_word] += 1
    return BoW_frequency

def get_meaning(file_dir): 
    """PDFファイルのパスを受け取り,{'英単語': '辞書に記載されている意味'}のdictを返す
    Args:
        file_dir (_str_): PDFファイルのパス

    Returns: 
        _dict_: 英単語がkey,英和辞典に記載されている意味の文字列がvalueになったdict
    """
    BoW_meaning = {}
    lemmatized_words = lemmatization(file_dir)
    for lemmatized_word in lemmatized_words:
        if (lemmatized_word not in stop_words) and (len(lemmatized_word) > 1):
            # BoW_meaning: {'単語': '辞書のエントリー'}の辞書
            meaning = ejdict.get(lemmatized_word, '') # 辞書に存在しない場合空の文字列を暫定のmeaningとして保持する
            BoW_meaning[lemmatized_word] = meaning
                        
    return BoW_meaning
