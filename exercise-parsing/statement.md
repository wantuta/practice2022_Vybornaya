Расширьте парсеры из модуля [nlparse](nlparse.py) одним из следующих способов:

1. Опциональный парсер:
   - вызывает нижележащий парсер;
     в том случае, если нижележащий парсер не вернул ничего,
     возвращает пустую составляющую

   Например:
   - `OptionalParser(word('a'))(['a', 'b'])` эквивалентно `word('a')(['a', 'b'])`
   - `OptionalParser(word('a'))(['b', 'c'])` вернет пару
     `Constituent(tag=None, children=(), words=()), ['b', 'c']`

2. Парсер-звездочка:
   - вызывает нижележащий парсер ноль или более раз,
     детьми составляющей результата должны быть составляющие,
     возвращаемые нижележащим парсером

   Например:
   - `StarParser(word('a'))(['a', 'b'])` вернет пару:
     `Constituent(tag=None,
                  children=(Constituent(tag=None, words=('a',), children=()),),
                  words=('a',)), ['b']`
   - `StarParser(word('a') | word('b'))*['a', 'b', 'c'])` вернет пару:
     `Constituent(tag=None,
                  children=(Constituent(tag=None, words=('a',), children=()),
                            Constituent(tag=None, words=('b',), children=())),
                  words=('a', 'b')), ['c']`
   - `StarParser(word('a') | word('b'))(['a', 'b', 'b'])` вернет пару:
     `Constituent(tag=None,
                  children=(Constituent(tag=None, words=('a',), children=()),
                            Constituent(tag=None, words=('b',), children=()),
                            Constituent(tag=None, words=('b',), children=()))
                  words=('a', 'b', 'b')), []`
   - `StarParser(word('a') | word('b'))(['c'])` вернет пару:
        `Constituent(tag=None, children=(), words=()), ['c']`


3. Парсер неупорядоченной конкатенации:
   - парсер должен вызвать каждый из своих дочерних парсеров по одному разу,
     но в любом порядке.

   Например:
   - `UnorderedParser([word('a'), word('b')])(['a', 'b'])` эквивалентно `(word('a') + word('b'))(['a', 'b'])`
   - `UnorderedParser([word('a'), word('b')])(['b', 'a'])` эквивалентно `(word('b') + word('a'))(['b', 'a'])`
   - `UnorderedParser([word('a'), word('b')])(['a', 'b', 'a'])` вернет пару:
     `Constituent(tag=None,
                  children=(Constituent(tag=None, words=('a',), children=()),
                            Constituent(tag=None, words=('b',), children=())),
                  words=('a', 'b')), ['c'])`
   - `UnorderedParser([word('a'), word('b')])(['a', 'c'])` не вернет ни одного результата
   - `UnorderedParser([word('a'), word('b'), word('c')])(['a', 'c', 'b'])` вернет пару:
     `Constituent(tag=None,
                  children=(Constituent(tag=None, words=('a',), children=()),
                            Constituent(tag=None, words=('c',), children=()),
                            Constituent(tag=None, words=('b',), children=())),
                  words=('a', 'c', 'b')), [])`

4. Парсер согласования:
   - парсер аналогичен конкатенации, но возвращает только конструкции, согласованные
     по какому-то категориальному признаку.

   Здесь мы предполагаем, что категориальная метка теперь не строка, а ассоциативный массив
   с элементами типа pos, number и т.п.

   Допустим:

   ```
   N = (word('fox') | word('wolf') | word('sheep')) @ {'pos':'N', 'number':'Sg'} |
       (word('foxes') | word('wolves') | word('sheep')) @ {'pos':'N', 'number':'Pl'} |
   Adj = word('quick') @ {'pos':'Adj', 'number':'Sg'} |
         word('quick') @ {'pos':'Adj', 'number':'Pl'} |
          word('many') @ {'pos':'Adj', 'number':'Pl'}
   Compl = (word('a') | word('the')) @ {'pos':'Compl', 'number':'Sg'} |
           word('the') @ {'pos':'Compl', 'number':'Pl'}

   V = word('jump') @ {'pos':'V', 'number':'Pl'} |
       word('jumps') @ {'pos':'V', 'number':'Sg'} |
       word('jumped') @ {'pos':'V', 'number':'Sg'} |
       word('jumped') @ {'pos':'V', 'number':'Pl'} |

   NP0 = recursive(lambda NP0: (N | AgreementParser('number', Adj, NP0) @ 'NP')
   NP = AgreementParser('number', Compl, NP0) @ 'NP'

   S = AgreementParser('number', NP, V) @ 'S'
   ```

   Тогда следующие строки будут восприниматься парсером S как корректные:

   - `a fox jumps`
   - `a quick fox jumps`
   - `the quick foxes jump`
   - `a sheep jumps`
   - `the sheep jumps`
   - `the sheep jump`
   - `a fox jumped`
   - `the fox jumped`
   - `the foxes jumped`
   - `the many foxes jump` (да, тут мы отступаем от грамматики английского ;)

   а следующие нет:

   - `a fox jump`
   - `a quick fox jump`
   - `a quick foxes jump`
   - `a many fox jumps`
   - `the foxes jumps`
