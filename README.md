# Asterix-KSYGEN
Convert AST (Asterix Definitions Files) to Kaitai Struct (KSY) Definition Files.

Esta utilidad programada en python permite generar archivos KSY para KSC (Kaitai Struct Compiler) a partir de las definiciones de Categorias Asterix que se encuentran en el proyecto "Asterix Defnition": https://zoranbosnjak.github.io/asterix-specs/index.html.

Para generar los archivos se utilizan las definiciones en formato JSON.

Esta versión solo trabaja con definiciones de categorias pero no con Refs, que no se encuentra aún implementado.

Los archivos KSY generados, pueden ser compilados con ksc, el compilador de Kaitay Struct, (https://kaitai.io).
