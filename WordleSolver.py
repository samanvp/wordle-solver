import re
import sys

MAX_PROB = 1.0
PUZZLE_SIZE = 5
GREEN_COEFF = 1.6
NUM_TOP_WORDS = 7

RUSSIAN_CORPUS = '../WordleSolver/Russian-words.txt'
ENGLISH_CORPUS = '../WordleSolver/wordle_complete_dictionary.txt'
ENGLISH_SOLUTIONS = '../WordleSolver/wordle_solutions_alphabetized.txt'

class CorpusLoader:
    def __init__(self, language):
        self.langague = language

    def getWords(self):
        if self.langague == 'eng':
            #return self.loadWords(ENGLISH_CORPUS)
            # Experimental
            return self.loadWords(ENGLISH_SOLUTIONS)
        elif self.langague == 'rus':
            return self.loadWords(RUSSIAN_CORPUS)
        else:
            raise ValueError('Unknown langage: {} please enter either "eng" or "rus"'.format(self.langague))

    def getLettersFreq(self):
        if self.langague == 'eng':
            return self.countLetters(self.loadWords(ENGLISH_SOLUTIONS))
        elif self.langague == 'rus':
            return self.countLetters(self.loadWords(RUSSIAN_CORPUS))
        else:
            raise ValueError('Unknown langage: {} please enter either "eng" or "rus"'.format(self.langague))

    def loadWords(self, filename, verbose=False):
        words = []
        with open(filename, 'r') as f:
            words = f.read().splitlines()
        if verbose:
            print('Conpus contains {} words.'.format(len(words)))
        
        selectedWords = []
        for word in words:
            if len(word) != PUZZLE_SIZE or word.find('-') != -1:
                continue
            selectedWords.append(word)

        if verbose:
            print('Corpus contains {} correct words with length {}'.format(len(selectedWords), PUZZLE_SIZE))
        return selectedWords

    def countLetters(self, words):
        counts = dict()
        for word in words:
            for i in range(PUZZLE_SIZE):
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
                counts[key] = value / (numWords * PUZZLE_SIZE)
            else:
                counts[key] = value / numWords
        
        # experimental: use position independent frequencies
        #for key, _ in counts.items():
        #    if key[0] != -1:
        #        counts[key] = counts[(-1, key[1])]
        return counts

class Solver:
    def __init__(self, words, lettersFreq):
        self.words = words
        self.lettersFreq = lettersFreq
   
    def getScore(self, word):
        scores = []
        for i in range(PUZZLE_SIZE):
            letter = word[i]
            key = (i, letter)
            if self.counts.get(key):
                scores.append(self.counts[key])
            else:
                scores.append(0.0)
        
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
        return [self.words[i] for i in topIndices]

    def validateFeedback(self):
        validFeedback = False
        feedback = ''
        print('Feedback: ', end='')
        while(not validFeedback):
            feedback = input()
            if len(feedback) != PUZZLE_SIZE or not re.fullmatch(r'[BbYyGg]*', feedback):
                print('Wrong feedback format, please try again:')
                continue
            validFeedback = True
        return feedback

    def parseFeedback(self, word, feedback):
        blacks = set()
        yellows = [None] * PUZZLE_SIZE
        greens = [None] * PUZZLE_SIZE
        for i in range(PUZZLE_SIZE):
            f = feedback[i]
            if f in ('B', 'b'):
                blacks.add(word[i])
            if f in ('Y', 'y'):
                yellows[i] = word[i]
            if f in ('G', 'g'):
                greens[i] = word[i]
        return (greens, yellows, blacks)    

    def initState(self):
        self.counts = self.lettersFreq.copy()
        self.greens = [None] * PUZZLE_SIZE
        self.yellows = [ [] for _ in range(PUZZLE_SIZE) ]
        self.blacks = set()
        self.guessNo = 0
 
    def updateState(self, latestGreens, latestYellows, latestBlacks):
        newGreens = [None] * PUZZLE_SIZE
        newYellows = [None] * PUZZLE_SIZE
        removedYellows = set()

        # First update the Greens
        for i in range(PUZZLE_SIZE):
            if latestGreens[i]:
                if self.greens[i]:
                    if self.greens[i] != latestGreens[i]:
                        raise ValueError('Position {} was Green letter {} and now it is {}'.format(i, self.greens[i], latestGreens[i]))
                else:
                    newGreenLetter = latestGreens[i]
                    self.greens[i] = newGreenLetter
                    newGreens[i] = newGreenLetter
                    # Now find out whether we previosly have seen this letter as a yellow one?
                    for j in range(PUZZLE_SIZE):
                        if newGreenLetter in self.yellows[j]:
                            removedYellows.add(newGreenLetter)
                            self.yellows[j].remove(newGreenLetter)
        # Next update the Yellows
        for i in range(PUZZLE_SIZE):
            if latestYellows[i]:
                if not latestYellows[i] in self.yellows[i]:
                    newYellowLetter = latestYellows[i]
                    self.yellows[i].append(newYellowLetter)
                    newYellows[i] = newYellowLetter
        # Blacks are only keep for debugging
        self.blacks = self.blacks.union(latestBlacks)
        return (newGreens, newYellows, removedYellows)

    def updateWeights(self, newGreens, newYellows, latestBlacks, removedYellows):
        for letter in latestBlacks:
            for i in range(PUZZLE_SIZE):
                key = (i, letter)
                self.counts[key] = -1 * PUZZLE_SIZE * MAX_PROB

        # Reverse the change made by an old Yellow letter
        for removedYellowLetter in removedYellows:
            for j in range(PUZZLE_SIZE):
                key = (j, removedYellowLetter)
                if self.counts[key] < 0:
                    continue
                else:
                    self.counts[key] = self.counts[(-1, removedYellowLetter)]

        # Apply new Yellows
        missingLettersCount = sum(elem is None for elem in self.greens)
        for i in range(PUZZLE_SIZE):
            if newYellows[i]:
                newYellowLetter = newYellows[i]
                key = (i, newYellowLetter)
                self.counts[key] = -1 * PUZZLE_SIZE * MAX_PROB
                for j in range(PUZZLE_SIZE):
                    if j == i or self.greens[j]:
                        continue
                    else:
                        key = (j, newYellowLetter)
                        if self.counts[key] > 0:
                            self.counts[key] = MAX_PROB / missingLettersCount

        # Apply Greens
        if self.guessNo > 3 or missingLettersCount <= 2:
            # We aggresivly set all green weights to converge faster
            for i in range(PUZZLE_SIZE):
                if self.greens[i]:
                    self.counts[(i, self.greens[i])] = MAX_PROB
        else:
            for i in range(PUZZLE_SIZE):
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
                if len(topWord) != 5 or not topWord.isalpha():
                    topWord = ''
                else:
                    topWord = topWord.lower()
        else:
            topWord = topWords[selectedIndex]
        return topWord

    def playGame(self, verbose=False):
        self.initState()
        feedbackColors = ''
        while(feedbackColors != 'ggggg'):
            self.guessNo += 1
            topWords = self.findTopWord()
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

        print('Solved by {} guesses!'.format(self.guessNo))

def main():
    #if len(sys.argv) != 2 or sys.argv[1] not in ['eng', 'rus']:
    #    print('Please run `python3 WordleSolver.py eng` or `python3 WordleSolver.py rus`')
    #    exit(1)
    #corpus = CorpusLoader(sys.argv[1])
    corpus = CorpusLoader('eng')
    solver = Solver(corpus.getWords(), corpus.getLettersFreq())
    solver.playGame(True)
    
if __name__ == '__main__':
    main()

