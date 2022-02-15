# wordle-solver
A universal Wordle solver that works with any language. All you need is a corpus for your language: a text file containing words, one in each line. I have so far tested this code using three langugages:
* English
* Persian
* Russian

Run one of the following commands to run the solver for one of the supported languages:

```python3 WordleSolver.py eng```

```python3 WordleSolver.py per```

```python3 WordleSolver.py rus```

If you like me to add support for another langauge please let me know.

# Methodology
## Letter Frequency
The main idea behind this algorithm is to use [letter frequency](https://en.wikipedia.org/wiki/Letter_frequency) to score each word. We simply look up the frequency of each letter and add them up to calculate the score of each word. Letter frequency is calculated using the list of [Wordle soltion words](https://github.com/AllValley/WordleDictionary). Here are top 5 words based on this simple huristic:
```
(1) >>>>>>> areae <<<<<<< score: 0.4599
(2) >>>>>>> eerie <<<<<<< score: 0.4552
(3) >>>>>>> resee <<<<<<< score: 0.455
(4) >>>>>>> raree <<<<<<< score: 0.453
(5) >>>>>>> arere <<<<<<< score: 0.453
```
As one can see we have *wasted* letters in each of these options. For example, word 'areae' has two 'a' and two 'e'. It would be better to include some other letters, even with lower frequency, instead of having repeated letters.

## Remove Repeated Letters
Our first improvement is to not double count repeated letters when we calculate each word's score. After this change we get the following top words:
```
(1)  >>>>>>> oater <<<<<<< score: 0.3969
(2)  >>>>>>> orate <<<<<<< score: 0.3969
(3)  >>>>>>> roate <<<<<<< score: 0.3969
(4)  >>>>>>> realo <<<<<<< score: 0.396
(5)  >>>>>>> alert <<<<<<< score: 0.3939
(6)  >>>>>>> alter <<<<<<< score: 0.3939
(7)  >>>>>>> artel <<<<<<< score: 0.3939
(8)  >>>>>>> later <<<<<<< score: 0.3939
(9)  >>>>>>> ratel <<<<<<< score: 0.3939
(10) >>>>>>> taler <<<<<<< score: 0.3939
```
As one can see, top 3 words have exact score because the are [anagrams](https://en.wikipedia.org/wiki/Anagram). Similarly words 5-10 all are anagrams. Now the question is how can we find the best option between anagrams.

## Positional Letter Frequency
Taking a quick look at the [Wordle solution words](https://github.com/AllValley/WordleDictionary/blob/main/wordle_solutions_alphabetized.txt) one can see there are 366 words that start with 's'. That's about 15% frequency which is singnificantly larger than 5.8% frequency of letter 's' independent of its position. To use this information we build a positional letter frequecy table that looks like this:

|     | 1 | 2 | 3 | 4 | 5 |
|:---:|---|---|---|---|---|
| a   |   |   |   |   |   |
| b   |   |   |   |   |   |
| c   |   |   |   |   |   |
| d   |   |   |   |   |   |
| ... |   |   |   |   |   |
| x   |   |   |   |   |   |
| y   |   |   |   |   |   |
| z   |   |   |   |   |   |

In other words we calculate a different frequecy value for each letter in each position. Using this table now we can assign different scores to anagrams. In fact when we use this method it changes the list of top words completely. Here are top 10 words:

```
(1) >>>>>>> saine <<<<<<< score: 0.6661
(2) >>>>>>> soare <<<<<<< score: 0.66
(3) >>>>>>> saice <<<<<<< score: 0.6531
(4) >>>>>>> slane <<<<<<< score: 0.6393
(5) >>>>>>> slate <<<<<<< score: 0.6207
(6) >>>>>>> soily <<<<<<< score: 0.6207
(7) >>>>>>> soave <<<<<<< score: 0.6143
(8) >>>>>>> samey <<<<<<< score: 0.6104
(9) >>>>>>> sauce <<<<<<< score: 0.6095
(10) >>>>>>> slice <<<<<<< score: 0.6086
```
## Opening Guess
So based on the previous list of top words, the best opening word is **saine**.
## Subsequent Guesses
After getting feedback for the first guess (in the form of green, yellow, and gray colors assigned to each letter) we update our positional letter frequency and then recalculate the score of all words to find the best next word.
### Gray Letters
We simply set the frequecy of all gray letters to a negative value making sure our next attemps will not include gray letters.
### Yellow Letters
We set the score of the yellow letter at the observed position to a negative value and all other unknown positions to large value (`MAX_PROB`) to encourage words that have the yellow letter in other positions.
### Green Letters
We set the frequecy of the green letter at the observer position to `MAX_PROB` and all other letters at that position to a negative value.

## Exploitation vs. Exploration Tradeoff
DRAFT

# Other Languages
## Persian
Here are the list of top opening words:

```
(1) >>>>>>> مرادی <<<<<<< score: 0.7361
(2) >>>>>>> موازی <<<<<<< score: 0.6852
(3) >>>>>>> مبانی <<<<<<< score: 0.6835
(4) >>>>>>> مکانی <<<<<<< score: 0.671
(5) >>>>>>> مجانی <<<<<<< score: 0.6699
(6) >>>>>>> معادی <<<<<<< score: 0.6614
(7) >>>>>>> موارد <<<<<<< score: 0.6552
```

Note when you enter the feedback for your guesses (green, yellow, black) you read the feedback right-to-left (as you read the word) and enter them one by one. For example consider the following example:

![alt text](./images/Persian-Wordle-example.jpg)

For the first guess the feedback must be 'bybby' as you read word 'مرادی'. The feedback for the second guess should be 'ybgyb' and so on.

## Russian
Here are the list of top opening words:

```
(1) >>>>>>> порка <<<<<<< score: 0.6324
(2) >>>>>>> полка <<<<<<< score: 0.6143
(3) >>>>>>> сотка <<<<<<< score: 0.6052
(4) >>>>>>> горка <<<<<<< score: 0.5853
(5) >>>>>>> норка <<<<<<< score: 0.5849
(6) >>>>>>> серна <<<<<<< score: 0.5835
(7) >>>>>>> совка <<<<<<< score: 0.5783
```

# Credit
For english I am using [Wordle's original dictionaries](https://github.com/AllValley/WordleDictionary). For russian I am using [this corpus](https://www.kaggle.com/bifus1/-russian-words). For persian I am using [this corpus](https://github.com/PersianWordle/Main).
