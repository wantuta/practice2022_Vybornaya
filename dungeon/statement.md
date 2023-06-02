Задание на усовершенствование парсера команд
============================================

1. Реализовать конструкцию "X of Y", которая бы находила
   объект, удовлетворяющий шаблону X внутри сущности, удовлетворяющей
   шаблону Y:
   ```
   > inspect the box
   The box contains:
   - a scroll
   - a ring
   - a magic wand
   > inspect a ring of the box
   This is some old rusty ring.
   ```
   
2. Реализовать поддержку множественного числа:
   ```
   > inspect a box
   Ambigous reference: a box
   > inspect all boxes
   There are 4 boxes in the room:
   - a red box
   - a black box
   - a white box
   - a green box
   > inspect a green box
   This box is green
   ```
   
   Для этого, в частности, метод `kind()` должен быть модифицирован:
   ```
   def kind(self, is_plural):
       ...
   ```
   При этом уже, конечно, не может оставаться `@property`.
   
   Альтернативный вариант: завести второй метод-свойство, `kind_pl`.


