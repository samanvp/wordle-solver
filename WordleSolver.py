import re
import sys


MAX_PROB = 1.0
DEFAULT_PUZZLE_SIZE = 5
GREEN_COEFF = 1.6
NUM_TOP_WORDS = 7

DUT_LEXICON = './Lexicons/dutch-all-words.txt'
DUT_SOLUTIONS = './Lexicons/dutch-puzzle-words.txt'
RUSSIAN_LEXICON = './Lexicons/Russian-words.txt'
PERSIAN_LEXICON = './Lexicons/persian-words-5letter.txt'
WORDLE_LEXICON = './Lexicons/wordle_complete_dictionary.txt'
WORDLE_SOLUTIONS = './Lexicons/wordle_solutions_alphabetized.txt'

class LexiconLoader:
    def __init__(self, language, puzzleSize):
        self.langague = language
        self.puzzleSize = puzzleSize

    def getWords(self):
        if self.langague == 'dut':
            return self.loadWords(DUT_LEXICON, True)
        elif self.langague == 'eng':
            return self.loadWords(WORDLE_LEXICON, True)
        elif self.langague == 'rus':
            return self.loadWords(RUSSIAN_LEXICON, True)
        elif self.langague == 'per':
            return self.loadWords(PERSIAN_LEXICON, True)
        else:
            raise ValueError('Unknown langage: {}'.format(self.langague))

    def getLettersFreq(self):
        if self.langague == 'dut':
            return self.countLetters(self.loadWords(DUT_SOLUTIONS))
        elif self.langague == 'eng':
            return self.countLetters(self.loadWords(WORDLE_SOLUTIONS))
        elif self.langague == 'rus':
            return self.countLetters(self.loadWords(RUSSIAN_LEXICON))
        elif self.langague == 'per':
            return self.countLetters(self.loadWords(PERSIAN_LEXICON))
        else:
            raise ValueError('Unknown langage: {}'.format(self.langague))

    def loadWords(self, filename, verbose=False):
        words = []
        with open(filename, 'r') as f:
            words = f.read().splitlines()

        if verbose:
            print('Lexicon contains {} words.'.format(len(words)))
         
        selectedWords = []
        for word in words:
            word = word.lower().strip()
            if re.search(r'[\s\-_]', word) or len(word) != self.puzzleSize:
                continue
            selectedWords.append(word)

        if verbose:
            print('Lexicon contains {} correct words with length {}.\n'.format(len(selectedWords), self.puzzleSize))
        return selectedWords

    def countLetters(self, words):
        counts = dict()
        for word in words:
            for i in range(self.puzzleSize):
                key = (i, word[i])
                if counts.get(key):
                    counts[key] += 1
                else:
                    counts[key] = 1

                # In (-1, *) keys we store position independent letter weights
                key = (-1, word[i])
                if counts.get(key):
                    counts[key] += 1
                else:
                    counts[key] = 1
        
        # Convert them to probability values in [0, 1] range
        numWords = len(words)
        for key, value in counts.items():
            if key[0] == -1:
                counts[key] = value / (numWords * self.puzzleSize)
            else:
                counts[key] = value / numWords
        
        # experimental: use position independent frequencies
        #for key, _ in counts.items():
        #    if key[0] != -1:
        #        counts[key] = counts[(-1, key[1])]
        return counts

class Solver:
    def __init__(self, words, lettersFreq, puzzleSize):
        self.words = words
        self.lettersFreq = lettersFreq
        self.puzzleSize = puzzleSize
   
    def getScore(self, word, removeDups=True):
        scores = []
        for i in range(self.puzzleSize):
            letter = word[i]
            key = (i, letter)
            if self.counts.get(key):
                scores.append(self.counts[key])
            else:
                key = (-1, letter)
                scores.append(self.counts[key])
        
        if removeDups:
            wordList = list(word)
            alreadyDeDuped = set()
            for letter in wordList:
                if letter in alreadyDeDuped:
                    continue
                dups = [i for i, x in enumerate(wordList) if x == letter]
                if len(dups) > 1:
                    subScores = [scores[i] for i in dups]
                    keep = subScores.index(max(subScores))
                    for i in range(len(dups)):
                        if i != keep:
                            if scores[dups[i]] == MAX_PROB or scores[dups[i]] == -1 * self.puzzleSize * MAX_PROB:
                                continue;  # This is is green letter, we do not subtract it's score.
                            scores[dups[i]] = 0
                    alreadyDeDuped.add(letter)
    
        return sum(scores)

    def findTopWord(self):
        scores = []
        for word in self.words:
            scores.append(self.getScore(word))

        topIndices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:NUM_TOP_WORDS]

        print('Best {} words are:'.format(NUM_TOP_WORDS))
        for i in range(len(topIndices)):
            print('({}) >>>>>>> {} <<<<<<< score: {}'.format(i+1, self.words[topIndices[i]], round(scores[topIndices[i]], 4)))
        if scores[topIndices[0]] < 0:
            raise ValueError('There is no word with positive score.')
        return [self.words[i] for i in topIndices]

    def validateFeedback(self):
        validFeedback = False
        feedback = ''
        print('What are the {} colors (g)Green, (y)Yellow, (b)Black: '.format(self.puzzleSize), end='')
        while(not validFeedback):
            feedback = input().lower()
            if len(feedback) != self.puzzleSize or not re.fullmatch(r'[byg]*', feedback):
                print('Wrong colors, please enter {} colors (g)Green, (y)Yellow, (b)Black: '.format(self.puzzleSize))
                continue
            validFeedback = True
        return feedback

    def parseFeedback(self, word, feedback):
        blacks = set()
        yellows = [None] * self.puzzleSize
        greens = [None] * self.puzzleSize
        for i in range(self.puzzleSize):
            f = feedback[i]
            if f == 'b':
                blacks.add(word[i])
            if f == 'y':
                yellows[i] = word[i]
            if f == 'g':
                greens[i] = word[i]
        return (greens, yellows, blacks)    

    def initState(self):
        self.counts = self.lettersFreq.copy()
        self.greens = [None] * self.puzzleSize
        self.yellows = [ [] for _ in range(self.puzzleSize) ]
        self.blacks = set()
        self.guessNo = 0
 
    def updateState(self, latestGreens, latestYellows, latestBlacks):
        newGreens = [None] * self.puzzleSize
        newYellows = [None] * self.puzzleSize
        removedYellows = set()

        # First update the Greens
        for i in range(self.puzzleSize):
            if latestGreens[i]:
                if self.greens[i]:
                    if self.greens[i] != latestGreens[i]:
                        raise ValueError('Position {} was Green letter {} and now it is {}'.format(i, self.greens[i], latestGreens[i]))
                else:
                    newGreenLetter = latestGreens[i]
                    self.greens[i] = newGreenLetter
                    newGreens[i] = newGreenLetter
                    # Now find out whether we previosly have seen this letter as a yellow one?
                    for j in range(self.puzzleSize):
                        if newGreenLetter in self.yellows[j]:
                            removedYellows.add(newGreenLetter)
                            self.yellows[j].remove(newGreenLetter)
        # Next update the Yellows
        for i in range(self.puzzleSize):
            if latestYellows[i]:
                if not latestYellows[i] in self.yellows[i]:
                    newYellowLetter = latestYellows[i]
                    self.yellows[i].append(newYellowLetter)
                    newYellows[i] = newYellowLetter
        # Blacks are only keep for debugging
        self.blacks = self.blacks.union(latestBlacks)
        return (newGreens, newYellows, removedYellows)

    def exploitGreens(self):
        for i in range(self.puzzleSize):
            if self.greens[i]:
                greenLetter = self.greens[i]
                for key, _ in self.counts.items():
                    if key[0] == i:
                        if key[1] == greenLetter:
                            self.counts[key] = MAX_PROB
                        else:
                            self.counts[key] =  -1 * self.puzzleSize * MAX_PROB

    def updateWeights(self, newGreens, newYellows, latestBlacks, removedYellows):
        for letter in latestBlacks:
            for i in range(self.puzzleSize):
                key = (i, letter)
                self.counts[key] = -1 * self.puzzleSize * MAX_PROB

        # Reverse the change made by an old Yellow letter
        for removedYellowLetter in removedYellows:
            for j in range(self.puzzleSize):
                key = (j, removedYellowLetter)
                if self.counts[key] < 0:
                    continue
                else:
                    self.counts[key] = self.counts[(-1, removedYellowLetter)]

        # Apply new Yellows
        missingLettersCount = sum(elem is None for elem in self.greens)
        for i in range(self.puzzleSize):
            if newYellows[i]:
                newYellowLetter = newYellows[i]
                key = (i, newYellowLetter)
                self.counts[key] = -1 * self.puzzleSize * MAX_PROB
                for j in range(self.puzzleSize):
                    if j == i or self.greens[j]:
                        continue
                    else:
                        key = (j, newYellowLetter)
                        if self.counts[key] > 0:
                            self.counts[key] = MAX_PROB / missingLettersCount

        # Apply Greens
        if self.guessNo > 3 or missingLettersCount <= 2:
            # We aggresivly set all green weights to converge faster
            self.exploitGreens()
        else:
            for i in range(self.puzzleSize):
                if newGreens[i]:
                    newGreenLetter = newGreens[i]
                    key = (i, newGreenLetter)
                    self.counts[key] = self.counts[key] * GREEN_COEFF

    def readUsedWord(self, topWords):
        selectedIndex = -1
        while(selectedIndex < 0 or selectedIndex > NUM_TOP_WORDS):
            print('Which word you used (1, 2, 3, ..)? for a word other than these options enter 0: ', end='')
            try:
                selectedIndex = int(input())
            except:
                print('Please enter a value between 1 and {}'.format(NUM_TOP_WORDS))
        selectedIndex -= 1 # This program might be used by someome other than a C++ programmer :D

        topWord = ''
        if selectedIndex == -1:
            while (not topWord):
                print('Please enter the word you used: ', end='')
                topWord = input()
                if len(topWord) != self.puzzleSize or not topWord.isalpha():
                    topWord = ''
                else:
                    topWord = topWord.lower()
        else:
            topWord = topWords[selectedIndex]
        return topWord

    def playGame(self, verbose=False):
        self.initState()
        feedbackColors = ''
        win = 'g' * self.puzzleSize
        while(feedbackColors != win):
            self.guessNo += 1
            try:
                topWords = self.findTopWord()
            except:
                print('No word in the current Lexicon matches the feedback.')
                break
            topWord = self.readUsedWord(topWords)
            feedbackColors = self.validateFeedback()
            (latestGreens, latestYellows, latestBlacks) = self.parseFeedback(topWord, feedbackColors)
            (newGreens, newYellows, removedYellows) = self.updateState(latestGreens, latestYellows, latestBlacks)
            self.updateWeights(newGreens, newYellows, latestBlacks, removedYellows)

            if verbose:
                print('Current Greens: ')
                print(self.greens)

                print('Current yellows: ')
                print(self.yellows)

                print('Current Blacks: ')
                print(sorted(list(self.blacks)))
        if feedbackColors == win:
            print('Solved by {} guesses!'.format(self.guessNo))
        else:
            print('Failed to find a solution after {} guesses.'.format(self.guessNo))

def showError(supportedLangs):
    print('Please run `python3 WordleSolver.py <LANG> [<SIZE>]`')
    print('where <LANG> can be one of the supported langages:  ', end='')
    for lang in supportedLangs:
        print(lang, end=' ')
    print('\n And <SIZE> is the length of the puzzle (default set to 5).')

def main():
    supportedLangs = ['dut', 'eng', 'rus', 'per']
    puzzleSize = DEFAULT_PUZZLE_SIZE 
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        showError(supportedLangs)
        exit(1)
    elif sys.argv[1] not in supportedLangs:
        showError(supportedLangs)
        exit(1)
    elif len(sys.argv) == 3:
        if not sys.argv[2].isnumeric():
            showError(supportedLangs)
            exit(1)
        else:
            puzzleSize = int(sys.argv[2])

    Lexicon = LexiconLoader(sys.argv[1], puzzleSize)
    solver = Solver(Lexicon.getWords(), Lexicon.getLettersFreq(), puzzleSize)
    solver.playGame(False)
    
if __name__ == '__main__':
    main()
