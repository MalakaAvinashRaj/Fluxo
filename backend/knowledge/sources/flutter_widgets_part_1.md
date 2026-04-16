
## Text

### Constructor
```dart
Text(
  String data, {
  Key? key,
  TextStyle? style,
  StrutStyle? strutStyle,
  TextAlign? textAlign,
  TextDirection? textDirection,
  Locale? locale,
  bool? softWrap,
  TextOverflow? overflow,
  double? textScaleFactor,
  int? maxLines,
  String? semanticsLabel,
  TextWidthBasis? textWidthBasis,
  TextHeightBehavior? textHeightBehavior,
})
```

### Common Properties
| Property | Type | Description |
|----------|------|-------------|
| `style` | `TextStyle?` | Font size, color, weight, decoration |
| `textAlign` | `TextAlign?` | left, right, center, justify, start, end |
| `overflow` | `TextOverflow?` | clip, ellipsis, fade, visible |
| `maxLines` | `int?` | Limits rendered lines |
| `softWrap` | `bool?` | Whether text wraps on soft line breaks |

### TextStyle Properties
```dart
TextStyle(
  Color? color,
  double? fontSize,         // e.g. 16.0
  FontWeight? fontWeight,   // FontWeight.bold, FontWeight.w500, etc.
  FontStyle? fontStyle,     // FontStyle.italic
  TextDecoration? decoration, // TextDecoration.underline, .lineThrough, .overline
  Color? decorationColor,
  double? letterSpacing,
  double? wordSpacing,
  double? height,           // line height multiplier
  String? fontFamily,       // e.g. 'Roboto'
  List<String>? fontFamilyFallback,
  Color? backgroundColor,
  TextOverflow? overflow,
)
```

### Examples
```dart
// Basic
Text('Hello Flutter')

// Styled
Text(
  'Welcome',
  style: TextStyle(
    fontSize: 24,
    fontWeight: FontWeight.bold,
    color: Colors.blue,
  ),
  textAlign: TextAlign.center,
  maxLines: 2,
  overflow: TextOverflow.ellipsis,
)

// Using Theme
Text(
  'Headline',
  style: Theme.of(context).textTheme.headlineMedium,
)
```

---

## RichText & TextSpan

### Constructor
```dart
RichText({
  Key? key,
  required InlineSpan text,
  TextAlign textAlign = TextAlign.start,
  TextDirection? textDirection,
  bool softWrap = true,
  TextOverflow overflow = TextOverflow.clip,
  double textScaleFactor = 1.0,
  int? maxLines,
  Locale? locale,
  StrutStyle? strutStyle,
  TextWidthBasis textWidthBasis = TextWidthBasis.parent,
  TextHeightBehavior? textHeightBehavior,
})
```

### Example
```dart
RichText(
  text: TextSpan(
    text: 'Hello ',
    style: DefaultTextStyle.of(context).style,
    children: [
      TextSpan(
        text: 'bold',
        style: TextStyle(fontWeight: FontWeight.bold),
      ),
      TextSpan(text: ' and '),
      TextSpan(
        text: 'colored',
        style: TextStyle(color: Colors.red),
      ),
    ],
  ),
)
```

---

## Container

### Constructor
```dart
Container({
  Key? key,
  AlignmentGeometry? alignment,
  EdgeInsetsGeometry? padding,
  Color? color,
  Decoration? decoration,
  Decoration? foregroundDecoration,
  double? width,
  double? height,
  BoxConstraints? constraints,
  EdgeInsetsGeometry? margin,
  Matrix4? transform,
  AlignmentGeometry? transformAlignment,
  Widget? child,
  Clip clipBehavior = Clip.none,
})
```

### Common Properties
| Property | Type | Description |
|----------|------|-------------|
| `color` | `Color?` | Background color (cannot use with decoration) |
| `decoration` | `BoxDecoration?` | Border, borderRadius, gradient, shadow |
| `padding` | `EdgeInsetsGeometry?` | Inner spacing |
| `margin` | `EdgeInsetsGeometry?` | Outer spacing |
| `width` / `height` | `double?` | Fixed dimensions |
| `constraints` | `BoxConstraints?` | Min/max width and height |
| `alignment` | `AlignmentGeometry?` | Aligns child within container |

### BoxDecoration
```dart
BoxDecoration(
  color: Colors.white,
  borderRadius: BorderRadius.circular(12),
  border: Border.all(color: Colors.grey, width: 1),
  boxShadow: [
    BoxShadow(
      color: Colors.black26,
      blurRadius: 8,
      offset: Offset(0, 4),
    ),
  ],
  gradient: LinearGradient(
    colors: [Colors.blue, Colors.purple],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  ),
  image: DecorationImage(
    image: AssetImage('assets/bg.png'),
    fit: BoxFit.cover,
  ),
)
```

### EdgeInsets Variants
```dart
EdgeInsets.all(16)
EdgeInsets.symmetric(horizontal: 16, vertical: 8)
EdgeInsets.only(left: 8, top: 4, right: 8, bottom: 4)
EdgeInsets.fromLTRB(8, 4, 8, 4)
EdgeInsetsDirectional.only(start: 16, end: 16)  // RTL-aware
```

### Examples
```dart
Container(
  width: 200,
  height: 100,
  margin: EdgeInsets.all(16),
  padding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
  decoration: BoxDecoration(
    color: Colors.white,
    borderRadius: BorderRadius.circular(8),
    boxShadow: [BoxShadow(color: Colors.black12, blurRadius: 4)],
  ),
  child: Text('Styled Container'),
)
```

---

## SizedBox

Used for fixed sizing and spacing.

```dart
SizedBox({
  Key? key,
  double? width,
  double? height,
  Widget? child,
})

// Named constructors
SizedBox.expand({Widget? child})   // fills all available space
SizedBox.shrink({Widget? child})   // zero size
SizedBox.fromSize({Widget? child, Size? size})
SizedBox.square({double? dimension, Widget? child})
```

### Usage
```dart
// Spacing between widgets
SizedBox(height: 16)
SizedBox(width: 8)

// Fixed size box
SizedBox(
  width: 100,
  height: 50,
  child: ElevatedButton(onPressed: () {}, child: Text('OK')),
)

// Expand to fill
SizedBox.expand(child: Container(color: Colors.blue))
```

---

## Column

Arranges children vertically.

### Constructor
```dart
Column({
  Key? key,
  MainAxisAlignment mainAxisAlignment = MainAxisAlignment.start,
  MainAxisSize mainAxisSize = MainAxisSize.max,
  CrossAxisAlignment crossAxisAlignment = CrossAxisAlignment.center,
  TextDirection? textDirection,
  VerticalDirection verticalDirection = VerticalDirection.down,
  TextBaseline? textBaseline,
  List<Widget> children = const [],
})
```

### MainAxisAlignment Values
| Value | Description |
|-------|-------------|
| `start` | Pack children at the top |
| `end` | Pack children at the bottom |
| `center` | Center children vertically |
| `spaceBetween` | Equal space between children |
| `spaceAround` | Equal space around children (half at ends) |
| `spaceEvenly` | Equal space everywhere |

### CrossAxisAlignment Values
| Value | Description |
|-------|-------------|
| `start` | Align to left edge |
| `end` | Align to right edge |
| `center` | Center horizontally (default) |
| `stretch` | Stretch to fill width |
| `baseline` | Align by text baseline |

### Example
```dart
Column(
  mainAxisAlignment: MainAxisAlignment.center,
  crossAxisAlignment: CrossAxisAlignment.stretch,
  children: [
    Text('Title', style: TextStyle(fontSize: 20)),
    SizedBox(height: 8),
    Text('Subtitle'),
    SizedBox(height: 16),
    ElevatedButton(onPressed: () {}, child: Text('Action')),
  ],
)
```

---

## Row

Arranges children horizontally. Same alignment properties as Column but axes are swapped.

### Constructor
```dart
Row({
  Key? key,
  MainAxisAlignment mainAxisAlignment = MainAxisAlignment.start,
  MainAxisSize mainAxisSize = MainAxisSize.max,
  CrossAxisAlignment crossAxisAlignment = CrossAxisAlignment.center,
  TextDirection? textDirection,
  VerticalDirection verticalDirection = VerticalDirection.down,
  TextBaseline? textBaseline,
  List<Widget> children = const [],
})
```

### Example
```dart
Row(
  mainAxisAlignment: MainAxisAlignment.spaceBetween,
  children: [
    Icon(Icons.star, color: Colors.amber),
    Text('Rating: 4.5'),
    TextButton(onPressed: () {}, child: Text('View')),
  ],
)

// Row with Expanded to fill remaining space
Row(
  children: [
    Icon(Icons.search),
    SizedBox(width: 8),
    Expanded(
      child: TextField(
        decoration: InputDecoration(hintText: 'Search...'),
      ),
    ),
  ],
)
```

---

## Stack

Overlaps children on top of each other (Z-axis layering).

### Constructor
```dart
Stack({
  Key? key,
  AlignmentGeometry alignment = AlignmentDirectional.topStart,
  TextDirection? textDirection,
  StackFit fit = StackFit.loose,
  Clip clipBehavior = Clip.hardEdge,
  List<Widget> children = const [],
})
```

### StackFit Values
- `loose` — children can be smaller than the Stack
- `expand` — children are forced to fill the Stack
- `passthrough` — constraints are passed through unchanged

### Example
```dart
Stack(
  alignment: Alignment.center,
  children: [
    // Background
    Container(
      width: 200,
      height: 200,
      color: Colors.blue,
    ),
    // Overlay text
    Text(
      'Overlay',
      style: TextStyle(color: Colors.white, fontSize: 20),
    ),
    // Positioned badge in top-right
    Positioned(
      top: 8,
      right: 8,
      child: CircleAvatar(
        radius: 12,
        backgroundColor: Colors.red,
        child: Text('3', style: TextStyle(color: Colors.white, fontSize: 10)),
      ),
    ),
  ],
)
```

---

## Scaffold

The primary structural widget for a Material Design screen.

### Constructor
```dart
Scaffold({
  Key? key,
  PreferredSizeWidget? appBar,
  Widget? body,
  Widget? floatingActionButton,
  FloatingActionButtonLocation? floatingActionButtonLocation,
  FloatingActionButtonAnimator? floatingActionButtonAnimator,
  List<Widget>? persistentFooterButtons,
  AlignmentDirectional persistentFooterAlignment = AlignmentDirectional.centerEnd,
  Widget? drawer,
  DrawerCallback? onDrawerChanged,
  Widget? endDrawer,
  DrawerCallback? onEndDrawerChanged,
  Widget? bottomNavigationBar,
  Widget? bottomSheet,
  Color? backgroundColor,
  bool? resizeToAvoidBottomInset,
  bool primary = true,
  DragStartBehavior drawerDragStartBehavior = DragStartBehavior.start,
  bool extendBody = false,
  bool extendBodyBehindAppBar = false,
  Color? drawerScrimColor,
  double? drawerEdgeDragWidth,
  bool drawerEnableOpenDragGesture = true,
  bool endDrawerEnableOpenDragGesture = true,
  String? restorationId,
})
```

### ScaffoldMessenger (for SnackBar)
```dart
// Show snackbar
ScaffoldMessenger.of(context).showSnackBar(
  SnackBar(content: Text('Hello!')),
);

// Show bottom sheet
showModalBottomSheet(
  context: context,
  builder: (context) => Container(height: 200, child: Text('Bottom Sheet')),
);
```

### Full Example
```dart
Scaffold(
  appBar: AppBar(title: Text('My App')),
  drawer: Drawer(child: ListView(children: [...])),
  body: Center(child: Text('Body')),
  floatingActionButton: FloatingActionButton(
    onPressed: () {},
    child: Icon(Icons.add),
  ),
  bottomNavigationBar: BottomNavigationBar(
    items: [
      BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Home'),
      BottomNavigationBarItem(icon: Icon(Icons.person), label: 'Profile'),
    ],
  ),
)
```

---

## AppBar

### Constructor
```dart
AppBar({
  Key? key,
  Widget? leading,
  bool automaticallyImplyLeading = true,
  Widget? title,
  List<Widget>? actions,
  Widget? flexibleSpace,
  PreferredSizeWidget? bottom,
  double? elevation,
  double? scrolledUnderElevation,
  Color? shadowColor,
  Color? surfaceTintColor,
  ShapeBorder? shape,
  Color? backgroundColor,
  Color? foregroundColor,
  IconThemeData? iconTheme,
  IconThemeData? actionsIconTheme,
  bool primary = true,
  bool? centerTitle,
  bool excludeHeaderSemantics = false,
  double? titleSpacing,
  double toolbarOpacity = 1.0,
  double bottomOpacity = 1.0,
  double? toolbarHeight,
  double? leadingWidth,
  TextStyle? toolbarTextStyle,
  TextStyle? titleTextStyle,
  SystemUiOverlayStyle? systemOverlayStyle,
  bool forceMaterialTransparency = false,
  Clip? clipBehavior,
})
```

### Example
```dart
AppBar(
  title: Text('Dashboard'),
  centerTitle: true,
  backgroundColor: Colors.deepPurple,
  foregroundColor: Colors.white,
  elevation: 4,
  leading: IconButton(
    icon: Icon(Icons.menu),
    onPressed: () => Scaffold.of(context).openDrawer(),
  ),
  actions: [
    IconButton(icon: Icon(Icons.search), onPressed: () {}),
    IconButton(icon: Icon(Icons.notifications), onPressed: () {}),
    PopupMenuButton<String>(
      onSelected: (value) {},
      itemBuilder: (context) => [
        PopupMenuItem(value: 'settings', child: Text('Settings')),
        PopupMenuItem(value: 'logout', child: Text('Logout')),
      ],
    ),
  ],
  bottom: TabBar(
    tabs: [Tab(text: 'Tab 1'), Tab(text: 'Tab 2')],
  ),
)
```

---

## ListView

### Constructors

```dart
// Basic - eager loading, good for small lists
ListView({
  Key? key,
  Axis scrollDirection = Axis.vertical,
  bool reverse = false,
  ScrollController? controller,
  bool? primary,
  ScrollPhysics? physics,
  bool shrinkWrap = false,
  EdgeInsetsGeometry? padding,
  double? itemExtent,
  Widget? prototypeItem,
  bool addAutomaticKeepAlives = true,
  bool addRepaintBoundaries = true,
  bool addSemanticIndexes = true,
  double? cacheExtent,
  List<Widget> children = const [],
  int? semanticChildCount,
  DragStartBehavior dragStartBehavior = DragStartBehavior.start,
  ScrollViewKeyboardDismissBehavior keyboardDismissBehavior = ScrollViewKeyboardDismissBehavior.manual,
  String? restorationId,
  Clip clipBehavior = Clip.hardEdge,
})

// Builder - lazy loading, preferred for long/dynamic lists
ListView.builder({
  required int? itemCount,
  required IndexedWidgetBuilder itemBuilder,
  double? itemExtent,
  ScrollController? controller,
  bool shrinkWrap = false,
  EdgeInsetsGeometry? padding,
  ScrollPhysics? physics,
  Axis scrollDirection = Axis.vertical,
  // ... other scroll properties
})

// Separated - lazy loading with separators
ListView.separated({
  required int itemCount,
  required IndexedWidgetBuilder itemBuilder,
  required IndexedWidgetBuilder separatorBuilder,
  // ... other scroll properties
})

// Custom - full control with SliverChildDelegate
ListView.custom({
  required SliverChildDelegate childrenDelegate,
  // ...
})
```

### Common ScrollPhysics
```dart
AlwaysScrollableScrollPhysics()   // always scrollable
BouncingScrollPhysics()           // iOS-style bounce
ClampingScrollPhysics()           // Android-style clamp
NeverScrollableScrollPhysics()    // disable scrolling
```

### Examples
```dart
// Simple list
ListView(
  padding: EdgeInsets.all(8),
  children: [
    ListTile(title: Text('Item 1')),
    ListTile(title: Text('Item 2')),
    ListTile(title: Text('Item 3')),
  ],
)

// Builder (recommended for dynamic data)
ListView.builder(
  itemCount: items.length,
  itemBuilder: (context, index) {
    return ListTile(
      leading: CircleAvatar(child: Text('${index + 1}')),
      title: Text(items[index].title),
      subtitle: Text(items[index].subtitle),
      trailing: Icon(Icons.chevron_right),
      onTap: () => Navigator.pushNamed(context, '/detail', arguments: items[index]),
    );
  },
)

// Separated
ListView.separated(
  itemCount: items.length,
  separatorBuilder: (context, index) => Divider(height: 1),
  itemBuilder: (context, index) => ListTile(title: Text(items[index])),
)

// Horizontal scrolling
ListView.builder(
  scrollDirection: Axis.horizontal,
  itemCount: 10,
  itemBuilder: (context, index) => Container(
    width: 120,
    margin: EdgeInsets.all(8),
    color: Colors.primaries[index % Colors.primaries.length],
  ),
)
```

---

## GridView

```dart
// Count-based grid
GridView.count(
  crossAxisCount: 2,              // number of columns
  crossAxisSpacing: 8,
  mainAxisSpacing: 8,
  padding: EdgeInsets.all(8),
  childAspectRatio: 1.0,          // width / height ratio
  children: List.generate(20, (i) => Card(child: Center(child: Text('$i')))),
)

// Builder with SliverGridDelegate
GridView.builder(
  itemCount: items.length,
  gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
    crossAxisCount: 3,
    crossAxisSpacing: 8,
    mainAxisSpacing: 8,
    childAspectRatio: 0.75,
  ),
  itemBuilder: (context, index) => Card(child: Text(items[index])),
)

// Flexible extent grid
GridView.builder(
  gridDelegate: SliverGridDelegateWithMaxCrossAxisExtent(
    maxCrossAxisExtent: 200,    // max width of each item
    crossAxisSpacing: 8,
    mainAxisSpacing: 8,
  ),
  itemBuilder: (context, index) => Container(color: Colors.blue),
)
```

---

## SingleChildScrollView

Makes a single widget scrollable when content overflows.

```dart
SingleChildScrollView({
  Key? key,
  Axis scrollDirection = Axis.vertical,
  bool reverse = false,
  EdgeInsetsGeometry? padding,
  bool? primary,
  ScrollPhysics? physics,
  ScrollController? controller,
  Widget? child,
  DragStartBehavior dragStartBehavior = DragStartBehavior.start,
  Clip clipBehavior = Clip.hardEdge,
  String? restorationId,
  ScrollViewKeyboardDismissBehavior keyboardDismissBehavior = ScrollViewKeyboardDismissBehavior.manual,
})
```

### Example
```dart
SingleChildScrollView(
  padding: EdgeInsets.all(16),
  child: Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      // Long form content that may overflow screen
      TextField(decoration: InputDecoration(labelText: 'Name')),
      SizedBox(height: 16),
      TextField(decoration: InputDecoration(labelText: 'Email')),
      // ... more fields
    ],
  ),
)
```

---

## GestureDetector

Detects various gestures without visual feedback.

### Constructor
```dart
GestureDetector({
  Key? key,
  Widget? child,
  GestureTapCallback? onTap,
  GestureTapCallback? onDoubleTap,
  GestureLongPressCallback? onLongPress,
  GestureDragStartCallback? onPanStart,
  GestureDragUpdateCallback? onPanUpdate,
  GestureDragEndCallback? onPanEnd,
  GestureTapDownCallback? onTapDown,
  GestureTapUpCallback? onTapUp,
  GestureTapCancelCallback? onTapCancel,
  GestureScaleStartCallback? onScaleStart,
  GestureScaleUpdateCallback? onScaleUpdate,
  GestureScaleEndCallback? onScaleEnd,
  HitTestBehavior? behavior,
  bool excludeFromSemantics = false,
  DragStartBehavior dragStartBehavior = DragStartBehavior.start,
})
```

### HitTestBehavior Values
- `deferToChild` — only detects if child handles it
- `opaque` — detects even in transparent areas
- `translucent` — detects in transparent areas + passes to behind

### Example
```dart
GestureDetector(
  onTap: () => print('Tapped'),
  onDoubleTap: () => print('Double tapped'),
  onLongPress: () => print('Long pressed'),
  onPanUpdate: (details) {
    setState(() {
      position += details.delta;  // drag
    });
  },
  child: Container(
    width: 100,
    height: 100,
    color: Colors.blue,
    child: Center(child: Text('Touch me')),
  ),
)
```

---

## InkWell

Like GestureDetector but with Material ripple effect.

```dart
InkWell({
  Key? key,
  Widget? child,
  GestureTapCallback? onTap,
  GestureTapCallback? onDoubleTap,
  GestureLongPressCallback? onLongPress,
  GestureTapDownCallback? onTapDown,
  GestureTapCancelCallback? onTapCancel,
  ValueChanged<bool>? onHighlightChanged,
  ValueChanged<bool>? onHover,
  MouseCursor? mouseCursor,
  Color? focusColor,
  Color? hoverColor,
  Color? highlightColor,
  MaterialStateProperty<Color?>? overlayColor,
  Color? splashColor,
  InteractiveInkFeatureFactory? splashFactory,
  double? radius,
  BorderRadius? borderRadius,
  ShapeBorder? customBorder,
  bool? enableFeedback = true,
  bool excludeFromSemantics = false,
  FocusNode? focusNode,
  bool canRequestFocus = true,
  ValueChanged<bool>? onFocusChange,
  bool autofocus = false,
})
```

### Example
```dart
// Must be inside a Material widget for ripple to show
Material(
  child: InkWell(
    onTap: () => Navigator.pushNamed(context, '/details'),
    borderRadius: BorderRadius.circular(8),
    child: Padding(
      padding: EdgeInsets.all(12),
      child: Row(
        children: [
          Icon(Icons.person),
          SizedBox(width: 8),
          Text('Profile'),
        ],
      ),
    ),
  ),
)
```

---

## Buttons

### ElevatedButton
```dart
ElevatedButton({
  required VoidCallback? onPressed,
  VoidCallback? onLongPress,
  ValueChanged<bool>? onHover,
  ValueChanged<bool>? onFocusChange,
  ButtonStyle? style,
  FocusNode? focusNode,
  bool autofocus = false,
  Clip? clipBehavior,
  WidgetStatesController? statesController,
  required Widget? child,
})

// Example
ElevatedButton(
  onPressed: () {},
  style: ElevatedButton.styleFrom(
    backgroundColor: Colors.blue,
    foregroundColor: Colors.white,
    padding: EdgeInsets.symmetric(horizontal: 24, vertical: 12),
    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
    elevation: 4,
    minimumSize: Size(120, 48),
  ),
  child: Text('Submit'),
)

// With icon
ElevatedButton.icon(
  onPressed: () {},
  icon: Icon(Icons.send),
  label: Text('Send'),
)
```

### TextButton
```dart
TextButton(
  onPressed: () {},
  style: TextButton.styleFrom(
    foregroundColor: Colors.blue,
    padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
  ),
  child: Text('Cancel'),
)
```

### OutlinedButton
```dart
OutlinedButton(
  onPressed: () {},
  style: OutlinedButton.styleFrom(
    foregroundColor: Colors.blue,
    side: BorderSide(color: Colors.blue, width: 1.5),
    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
  ),
  child: Text('Learn More'),
)
```

### IconButton
```dart
IconButton(
  icon: Icon(Icons.favorite),
  color: Colors.red,
  iconSize: 28,
  tooltip: 'Favorite',
  onPressed: () {},
)
```

### ButtonStyle (full control)
```dart
ButtonStyle(
  backgroundColor: MaterialStateProperty.resolveWith<Color>((states) {
    if (states.contains(MaterialState.disabled)) return Colors.grey;
    if (states.contains(MaterialState.pressed)) return Colors.blueAccent;
    return Colors.blue;
  }),
  foregroundColor: MaterialStateProperty.all(Colors.white),
  overlayColor: MaterialStateProperty.all(Colors.white24),
  shape: MaterialStateProperty.all(
    RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
  ),
  padding: MaterialStateProperty.all(EdgeInsets.all(16)),
  elevation: MaterialStateProperty.all(4),
  textStyle: MaterialStateProperty.all(TextStyle(fontSize: 16, fontWeight: FontWeight.bold)),
)
```

---

## TextField & TextFormField

### TextField Constructor
```dart
TextField({
  Key? key,
  TextEditingController? controller,
  FocusNode? focusNode,
  InputDecoration? decoration = const InputDecoration(),
  TextInputType? keyboardType,
  TextInputAction? textInputAction,
  TextCapitalization textCapitalization = TextCapitalization.none,
  TextStyle? style,
  TextAlign textAlign = TextAlign.start,
  bool autofocus = false,
  bool obscureText = false,
  int? maxLines = 1,
  int? minLines,
  int? maxLength,
  ValueChanged<String>? onChanged,
  VoidCallback? onEditingComplete,
  ValueChanged<String>? onSubmitted,
  List<TextInputFormatter>? inputFormatters,
  bool? enabled,
  bool readOnly = false,
  bool? showCursor,
  String obscuringCharacter = '•',
  GestureTapCallback? onTap,
  bool enableSuggestions = true,
  bool autocorrect = true,
  bool enableInteractiveSelection = true,
  TextSelectionControls? selectionControls,
  InputCounterWidgetBuilder? buildCounter,
  ScrollPhysics? scrollPhysics,
  Iterable<String>? autofillHints,
  String? restorationId,
})
```

### InputDecoration
```dart
InputDecoration(
  labelText: 'Email',
  hintText: 'Enter your email',
  helperText: 'We will never share your email',
  errorText: 'Invalid email',           // shows red error text
  prefixIcon: Icon(Icons.email),
  suffixIcon: IconButton(
    icon: Icon(Icons.clear),
    onPressed: () => controller.clear(),
  ),
  prefixText: '+1 ',
  suffixText: '.com',
  border: OutlineInputBorder(
    borderRadius: BorderRadius.circular(8),
  ),
  enabledBorder: OutlineInputBorder(
    borderSide: BorderSide(color: Colors.grey),
  ),
  focusedBorder: OutlineInputBorder(
    borderSide: BorderSide(color: Colors.blue, width: 2),
  ),
  errorBorder: OutlineInputBorder(
    borderSide: BorderSide(color: Colors.red),
  ),
  filled: true,
  fillColor: Colors.grey[100],
  contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
  isDense: true,           // reduces vertical size
  floatingLabelBehavior: FloatingLabelBehavior.always,
)
```

### TextFormField (used inside Form widget)
```dart
TextFormField(
  controller: _emailController,
  keyboardType: TextInputType.emailAddress,
  textInputAction: TextInputAction.next,
  decoration: InputDecoration(
    labelText: 'Email',
    prefixIcon: Icon(Icons.email),
    border: OutlineInputBorder(),
  ),
  validator: (value) {
    if (value == null || value.isEmpty) return 'Email is required';
    if (!value.contains('@')) return 'Enter a valid email';
    return null;  // null means valid
  },
  onSaved: (value) => _email = value!,
)
```

### TextInputType Values
```dart
TextInputType.text
TextInputType.multiline
TextInputType.number
TextInputType.phone
TextInputType.emailAddress
TextInputType.url
TextInputType.visiblePassword
TextInputType.name
TextInputType.streetAddress
TextInputType.datetime
```

### TextInputFormatters
```dart
import 'package:flutter/services.dart';

inputFormatters: [
  FilteringTextInputFormatter.digitsOnly,                    // only digits
  FilteringTextInputFormatter.allow(RegExp(r'[a-zA-Z]')),   // only letters
  FilteringTextInputFormatter.deny(RegExp(r'\s')),           // no spaces
  LengthLimitingTextInputFormatter(10),                      // max 10 chars
]
```

---

## Image

```dart
// Asset image
Image.asset(
  'assets/images/logo.png',
  width: 200,
  height: 100,
  fit: BoxFit.contain,
)

// Network image
Image.network(
  'https://example.com/photo.jpg',
  width: 300,
  height: 200,
  fit: BoxFit.cover,
  loadingBuilder: (context, child, loadingProgress) {
    if (loadingProgress == null) return child;
    return CircularProgressIndicator(
      value: loadingProgress.expectedTotalBytes != null
          ? loadingProgress.cumulativeBytesLoaded / loadingProgress.expectedTotalBytes!
          : null,
    );
  },
  errorBuilder: (context, error, stackTrace) =>
      Icon(Icons.broken_image, size: 50),
)

// File image
Image.file(File('/path/to/image.jpg'))

// Memory image
Image.memory(Uint8List bytes)
```

### BoxFit Values
| Value | Description |
|-------|-------------|
| `fill` | Stretch to fill (may distort) |
| `contain` | Fit inside box, preserve aspect ratio |
| `cover` | Fill box, crop excess, preserve aspect ratio |
| `fitWidth` | Fit width, may crop vertically |
| `fitHeight` | Fit height, may crop horizontally |
| `none` | Center without resizing |
| `scaleDown` | Same as contain but never scale up |

---

## Icon

```dart
Icon(
  Icons.favorite,        // from Material icons
  size: 24.0,
  color: Colors.red,
  semanticLabel: 'Favorite',
  textDirection: TextDirection.ltr,
)

// Cupertino icons (iOS style)
import 'package:flutter/cupertino.dart';
Icon(CupertinoIcons.heart_fill)

// Custom icon from font
Icon(
  IconData(0xe800, fontFamily: 'MyCustomIcons'),
)
```

---

## Card

```dart
Card({
  Key? key,
  Color? color,
  Color? shadowColor,
  Color? surfaceTintColor,
  double? elevation,
  ShapeBorder? shape,
  bool borderOnForeground = true,
  EdgeInsetsGeometry? margin,
  Clip? clipBehavior,
  Widget? child,
  bool semanticContainer = true,
})

// Example
Card(
  elevation: 4,
  margin: EdgeInsets.all(8),
  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
  child: Padding(
    padding: EdgeInsets.all(16),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Card Title', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
        SizedBox(height: 8),
        Text('Card content goes here'),
        ButtonBar(
          children: [
            TextButton(onPressed: () {}, child: Text('ACTION 1')),
            TextButton(onPressed: () {}, child: Text('ACTION 2')),
          ],
        ),
      ],
    ),
  ),
)
```

---

## Padding & Margin

Padding is a widget. Margin is a property of Container.

```dart
// As widget
Padding(
  padding: EdgeInsets.all(16),
  child: Text('Padded text'),
)

// Symmetric
Padding(
  padding: EdgeInsets.symmetric(horizontal: 24, vertical: 12),
  child: Widget(),
)

// Via Container margin
Container(
  margin: EdgeInsets.only(top: 16, bottom: 8),
  child: Widget(),
)
```

---

## Expanded & Flexible

Used inside Row, Column, or Flex to control how children share space.

```dart
// Expanded - takes all remaining space
Row(
  children: [
    Icon(Icons.star),
    Expanded(
      child: Text('This text fills remaining space', overflow: TextOverflow.ellipsis),
    ),
    Icon(Icons.more_vert),
  ],
)

// Flexible - takes space proportionally but can be smaller
Row(
  children: [
    Flexible(flex: 2, child: Container(color: Colors.red)),   // 2/3 of space
    Flexible(flex: 1, child: Container(color: Colors.blue)),  // 1/3 of space
  ],
)

// Multiple expanded with flex
Column(
  children: [
    Expanded(flex: 3, child: Container(color: Colors.blue)),    // 60%
    Expanded(flex: 2, child: Container(color: Colors.green)),   // 40%
  ],
)
```

---

## Wrap

Like Row/Column but wraps to the next line when space runs out.

```dart
Wrap({
  Key? key,
  Axis direction = Axis.horizontal,
  WrapAlignment alignment = WrapAlignment.start,
  double spacing = 0.0,          // main-axis spacing between children
  WrapAlignment runAlignment = WrapAlignment.start,
  double runSpacing = 0.0,       // cross-axis spacing between runs
  WrapCrossAlignment crossAxisAlignment = WrapCrossAlignment.start,
  TextDirection? textDirection,
  VerticalDirection verticalDirection = VerticalDirection.down,
  Clip clipBehavior = Clip.none,
  List<Widget> children = const [],
})

// Example: chip group
Wrap(
  spacing: 8,
  runSpacing: 4,
  children: tags.map((tag) => Chip(
    label: Text(tag),
    onDeleted: () => removeTag(tag),
  )).toList(),
)
```

---

## Positioned

Must be a direct child of Stack.

```dart
Positioned({
  Key? key,
  double? left,
  double? top,
  double? right,
  double? bottom,
  double? width,
  double? height,
  required Widget child,
})

// Fill entire stack
Positioned.fill(child: Container(color: Colors.black54))

// Example
Stack(
  children: [
    Image.asset('background.png', fit: BoxFit.cover),
    Positioned(
      bottom: 16,
      left: 16,
      right: 16,
      child: Text('Caption', style: TextStyle(color: Colors.white)),
    ),
    Positioned(
      top: 8,
      right: 8,
      child: IconButton(icon: Icon(Icons.close, color: Colors.white), onPressed: () {}),
    ),
  ],
)
```

---

## Navigator & Routes

### Imperative Navigation (Navigator)
```dart
// Push a new screen
Navigator.push(
  context,
  MaterialPageRoute(builder: (context) => DetailScreen()),
)

// Push and wait for result
final result = await Navigator.push<String>(
  context,
  MaterialPageRoute(builder: (context) => SelectionScreen()),
)

// Pop (go back)
Navigator.pop(context)

// Pop with result
Navigator.pop(context, 'selected_value')

// Push named route
Navigator.pushNamed(context, '/detail', arguments: {'id': 42})

// Push and replace current route
Navigator.pushReplacement(
  context,
  MaterialPageRoute(builder: (context) => HomeScreen()),
)

// Push and clear stack
Navigator.pushAndRemoveUntil(
  context,
  MaterialPageRoute(builder: (context) => LoginScreen()),
  (route) => false,   // removes all routes
)

// Pop until a route
Navigator.popUntil(context, ModalRoute.withName('/home'))
```

### Receiving arguments in named routes
```dart
// In the destination widget
final args = ModalRoute.of(context)!.settings.arguments as Map<String, dynamic>;
final id = args['id'];
```

### PageRouteBuilder (custom transitions)
```dart
Navigator.push(
  context,
  PageRouteBuilder(
    pageBuilder: (context, animation, secondaryAnimation) => DetailScreen(),
    transitionsBuilder: (context, animation, secondaryAnimation, child) {
      return FadeTransition(opacity: animation, child: child);
    },
    transitionDuration: Duration(milliseconds: 300),
  ),
)
```

---

## AlertDialog & BottomSheet

### AlertDialog
```dart
showDialog<bool>(
  context: context,
  barrierDismissible: false,   // prevent dismissal by tapping outside
  builder: (context) => AlertDialog(
    title: Text('Confirm Delete'),
    content: Text('Are you sure you want to delete this item?'),
    actions: [
      TextButton(
        onPressed: () => Navigator.pop(context, false),
        child: Text('Cancel'),
      ),
      ElevatedButton(
        onPressed: () => Navigator.pop(context, true),
        style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
        child: Text('Delete'),
      ),
    ],
    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
  ),
)

// Await result
final confirmed = await showDialog<bool>(...);
if (confirmed == true) { /* proceed */ }
```

### BottomSheet (modal)
```dart
showModalBottomSheet(
  context: context,
  isScrollControlled: true,        // allows full height
  backgroundColor: Colors.transparent,
  builder: (context) => DraggableScrollableSheet(
    initialChildSize: 0.5,
    minChildSize: 0.25,
    maxChildSize: 0.95,
    builder: (context, scrollController) => Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      child: ListView(
        controller: scrollController,
        children: [/* items */],
      ),
    ),
  ),
)
```

---

## SnackBar

```dart
ScaffoldMessenger.of(context).showSnackBar(
  SnackBar(
    content: Text('Item saved successfully'),
    backgroundColor: Colors.green,
    duration: Duration(seconds: 3),
    action: SnackBarAction(
      label: 'Undo',
      textColor: Colors.white,
      onPressed: () {/* undo logic */},
    ),
    behavior: SnackBarBehavior.floating,   // floats above bottom nav
    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
    margin: EdgeInsets.all(8),
  ),
)

// Dismiss existing before showing new
ScaffoldMessenger.of(context)
  ..hideCurrentSnackBar()
  ..showSnackBar(SnackBar(content: Text('New message')));
```

---

## Progress Indicators

```dart
// Indeterminate circular
CircularProgressIndicator(
  color: Colors.blue,
  strokeWidth: 4,
)

// Determinate circular
CircularProgressIndicator(
  value: 0.7,    // 0.0 to 1.0
  backgroundColor: Colors.grey[200],
  color: Colors.blue,
)

// Indeterminate linear
LinearProgressIndicator(
  color: Colors.blue,
  backgroundColor: Colors.grey[200],
)

// Determinate linear
LinearProgressIndicator(
  value: progress,   // 0.0 to 1.0
  minHeight: 8,
  color: Colors.green,
  backgroundColor: Colors.grey[200],
)

// Adaptive (platform-specific style)
CircularProgressIndicator.adaptive()
```

---

## Divider & VerticalDivider

```dart
Divider(
  height: 1,          // total space occupied (not line thickness)
  thickness: 1,       // actual line thickness
  color: Colors.grey[300],
  indent: 16,         // left indent
  endIndent: 16,      // right indent
)

VerticalDivider(
  width: 1,
  thickness: 1,
  color: Colors.grey[300],
  indent: 8,
  endIndent: 8,
)
```

---

## Checkbox, Radio, Switch

### Checkbox
```dart
Checkbox(
  value: _isChecked,
  tristate: false,
  activeColor: Colors.blue,
  checkColor: Colors.white,
  onChanged: (bool? value) {
    setState(() => _isChecked = value!);
  },
)

// CheckboxListTile (with label)
CheckboxListTile(
  title: Text('Accept Terms'),
  subtitle: Text('By checking this you agree to...'),
  value: _agreed,
  onChanged: (value) => setState(() => _agreed = value!),
  controlAffinity: ListTileControlAffinity.leading,
)
```

### Radio
```dart
// Must group by value type
Radio<String>(
  value: 'option1',
  groupValue: _selectedOption,
  onChanged: (value) => setState(() => _selectedOption = value!),
)

// RadioListTile
RadioListTile<String>(
  title: Text('Option 1'),
  value: 'option1',
  groupValue: _selectedOption,
  onChanged: (value) => setState(() => _selectedOption = value!),
)
```

### Switch
```dart
Switch(
  value: _isEnabled,
  activeColor: Colors.blue,
  onChanged: (value) => setState(() => _isEnabled = value),
)

// SwitchListTile
SwitchListTile(
  title: Text('Dark Mode'),
  subtitle: Text('Enable dark theme'),
  value: _darkMode,
  onChanged: (value) => setState(() => _darkMode = value),
)
```

---

## Slider

```dart
Slider(
  value: _currentValue,
  min: 0.0,
  max: 100.0,
  divisions: 10,             // creates discrete steps
  label: '${_currentValue.round()}',
  activeColor: Colors.blue,
  inactiveColor: Colors.grey[300],
  thumbColor: Colors.blue,
  onChanged: (value) => setState(() => _currentValue = value),
  onChangeStart: (value) => print('Started at $value'),
  onChangeEnd: (value) => print('Ended at $value'),
)

// RangeSlider
RangeSlider(
  values: _rangeValues,    // RangeValues(20, 80)
  min: 0,
  max: 100,
  divisions: 20,
  labels: RangeLabels(
    _rangeValues.start.round().toString(),
    _rangeValues.end.round().toString(),
  ),
  onChanged: (values) => setState(() => _rangeValues = values),
)
```

---

## Dropdown

### DropdownButton
```dart
DropdownButton<String>(
  value: _selectedCity,
  hint: Text('Select city'),
  isExpanded: true,
  underline: SizedBox.shrink(),  // removes default underline
  icon: Icon(Icons.keyboard_arrow_down),
  items: cities.map((city) => DropdownMenuItem<String>(
    value: city,
    child: Text(city),
  )).toList(),
  onChanged: (value) => setState(() => _selectedCity = value),
)
```

### DropdownButtonFormField (inside Form)
```dart
DropdownButtonFormField<String>(
  value: _selectedCountry,
  decoration: InputDecoration(
    labelText: 'Country',
    border: OutlineInputBorder(),
  ),
  items: countries.map((c) => DropdownMenuItem(value: c, child: Text(c))).toList(),
  validator: (value) => value == null ? 'Please select a country' : null,
  onChanged: (value) => setState(() => _selectedCountry = value),
  onSaved: (value) => _country = value!,
)
```

---

## TabBar & TabBarView

```dart
class MyTabScreen extends StatefulWidget {
  @override
  State<MyTabScreen> createState() => _MyTabScreenState();
}

class _MyTabScreenState extends State<MyTabScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Tabs'),
        bottom: TabBar(
          controller: _tabController,
          tabs: [
            Tab(icon: Icon(Icons.home), text: 'Home'),
            Tab(icon: Icon(Icons.search), text: 'Search'),
            Tab(icon: Icon(Icons.person), text: 'Profile'),
          ],
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white60,
          indicatorColor: Colors.white,
          indicatorWeight: 3,
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: [
          HomeTab(),
          SearchTab(),
          ProfileTab(),
        ],
      ),
    );
  }
}
```

---

## Drawer

```dart
Drawer(
  child: ListView(
    padding: EdgeInsets.zero,
    children: [
      DrawerHeader(
        decoration: BoxDecoration(color: Colors.blue),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisAlignment: MainAxisAlignment.end,
          children: [
            CircleAvatar(radius: 30, backgroundImage: NetworkImage(userAvatarUrl)),
            SizedBox(height: 8),
            Text('John Doe', style: TextStyle(color: Colors.white, fontSize: 16)),
            Text('john@example.com', style: TextStyle(color: Colors.white70)),
          ],
        ),
      ),
      ListTile(
        leading: Icon(Icons.home),
        title: Text('Home'),
        selected: _currentRoute == '/',
        onTap: () {
          Navigator.pushReplacementNamed(context, '/');
          Navigator.pop(context);  // close drawer
        },
      ),
      ListTile(
        leading: Icon(Icons.settings),
        title: Text('Settings'),
        onTap: () {
          Navigator.pop(context);
          Navigator.pushNamed(context, '/settings');
        },
      ),
      Divider(),
      ListTile(
        leading: Icon(Icons.logout, color: Colors.red),
        title: Text('Logout', style: TextStyle(color: Colors.red)),
        onTap: () => _logout(context),
      ),
    ],
  ),
)
```

---

## BottomNavigationBar

```dart
BottomNavigationBar(
  currentIndex: _currentIndex,
  selectedItemColor: Colors.blue,
  unselectedItemColor: Colors.grey,
  backgroundColor: Colors.white,
  type: BottomNavigationBarType.fixed,  // or .shifting
  elevation: 8,
  onTap: (index) => setState(() => _currentIndex = index),
  items: [
    BottomNavigationBarItem(
      icon: Icon(Icons.home_outlined),
      activeIcon: Icon(Icons.home),
      label: 'Home',
    ),
    BottomNavigationBarItem(
      icon: Icon(Icons.search_outlined),
      activeIcon: Icon(Icons.search),
      label: 'Discover',
    ),
    BottomNavigationBarItem(
      icon: Icon(Icons.notifications_outlined),
      activeIcon: Icon(Icons.notifications),
      label: 'Alerts',
    ),
    BottomNavigationBarItem(
      icon: Icon(Icons.person_outline),
      activeIcon: Icon(Icons.person),
      label: 'Profile',
    ),
  ],
)
```

---

## FloatingActionButton

```dart
FloatingActionButton(
  onPressed: () {},
  tooltip: 'Add item',
  backgroundColor: Colors.blue,
  foregroundColor: Colors.white,
  elevation: 6,
  shape: CircleBorder(),
  child: Icon(Icons.add),
)

// Extended FAB (with label)
FloatingActionButton.extended(
  onPressed: () {},
  icon: Icon(Icons.add),
  label: Text('New Post'),
)

// Small FAB
FloatingActionButton.small(
  onPressed: () {},
  child: Icon(Icons.add),
)

// Large FAB
FloatingActionButton.large(
  onPressed: () {},
  child: Icon(Icons.add),
)
```

---

## AnimatedContainer

Smoothly animates between property changes.

```dart
AnimatedContainer(
  duration: Duration(milliseconds: 300),
  curve: Curves.easeInOut,
  width: _expanded ? 200 : 100,
  height: _expanded ? 200 : 100,
  color: _expanded ? Colors.blue : Colors.red,
  padding: EdgeInsets.all(_expanded ? 24 : 8),
  decoration: BoxDecoration(
    borderRadius: BorderRadius.circular(_expanded ? 32 : 8),
  ),
  child: Text('Animated!'),
)

// Toggle:
onTap: () => setState(() => _expanded = !_expanded)
```

### Other Animated Widgets
```dart
AnimatedOpacity(opacity: _visible ? 1.0 : 0.0, duration: Duration(milliseconds: 300), child: widget)
AnimatedPadding(padding: _padding, duration: Duration(milliseconds: 200), child: widget)
AnimatedAlign(alignment: _alignment, duration: Duration(milliseconds: 200), child: widget)
AnimatedSwitcher(duration: Duration(milliseconds: 300), child: _current)  // cross-fade between children
AnimatedSize(duration: Duration(milliseconds: 200), child: widget)
```

---

## FutureBuilder

```dart
FutureBuilder<List<User>>(
  future: fetchUsers(),
  builder: (context, snapshot) {
    if (snapshot.connectionState == ConnectionState.waiting) {
      return Center(child: CircularProgressIndicator());
    }
    if (snapshot.hasError) {
      return Center(child: Text('Error: ${snapshot.error}'));
    }
    if (!snapshot.hasData || snapshot.data!.isEmpty) {
      return Center(child: Text('No users found'));
    }
    final users = snapshot.data!;
    return ListView.builder(
      itemCount: users.length,
      itemBuilder: (context, index) => ListTile(title: Text(users[index].name)),
    );
  },
)
```

### ConnectionState Values
- `none` — Future is null
- `waiting` — awaiting result
- `active` — not used with Future (only Stream)
- `done` — completed (check hasError / hasData)

---

## StreamBuilder

```dart
StreamBuilder<int>(
  stream: _counterStream,
  initialData: 0,
  builder: (context, snapshot) {
    if (snapshot.connectionState == ConnectionState.waiting) {
      return CircularProgressIndicator();
    }
    if (snapshot.hasError) {
      return Text('Error: ${snapshot.error}');
    }
    return Text('Count: ${snapshot.data}');
  },
)
```

---

## ValueListenableBuilder

Rebuilds only when the `ValueListenable` changes.

```dart
final _counter = ValueNotifier<int>(0);

ValueListenableBuilder<int>(
  valueListenable: _counter,
  builder: (context, value, child) {
    return Column(
      children: [
        // child is the subtree that doesn't need rebuilding
        child!,
        Text('Count: $value'),
      ],
    );
  },
  child: Text('Static child - not rebuilt'),  // passed as child arg
)

// Increment: _counter.value++
// Dispose: _counter.dispose()
```

---

## LayoutBuilder

Builds based on the parent's constraints.

```dart
LayoutBuilder(
  builder: (context, constraints) {
    if (constraints.maxWidth > 600) {
      return DesktopLayout();   // wide screen
    } else {
      return MobileLayout();    // narrow screen
    }
  },
)
```

---

## MediaQuery

Provides information about the device screen.

```dart
// Inside a build method
final size = MediaQuery.of(context).size;
final width = size.width;
final height = size.height;
final padding = MediaQuery.of(context).padding;          // device safe areas
final viewInsets = MediaQuery.of(context).viewInsets;   // keyboard height
final orientation = MediaQuery.of(context).orientation; // portrait / landscape
final textScaleFactor = MediaQuery.of(context).textScaleFactor;
final platformBrightness = MediaQuery.of(context).platformBrightness; // dark/light

// Check if keyboard is showing
final isKeyboardOpen = MediaQuery.of(context).viewInsets.bottom > 0;

// Responsive width
Container(
  width: MediaQuery.of(context).size.width * 0.8,  // 80% of screen width
)
```

---

## Theme & ThemeData

### Applying Theme
```dart
MaterialApp(
  theme: ThemeData(
    colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
    useMaterial3: true,
    textTheme: TextTheme(
      headlineLarge: TextStyle(fontSize: 32, fontWeight: FontWeight.bold),
      bodyMedium: TextStyle(fontSize: 14, color: Colors.black87),
    ),
    appBarTheme: AppBarTheme(
      backgroundColor: Colors.blue,
      foregroundColor: Colors.white,
      elevation: 0,
      centerTitle: true,
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        padding: EdgeInsets.symmetric(horizontal: 24, vertical: 12),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
      contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
    ),
    cardTheme: CardTheme(
      elevation: 2,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
    ),
  ),
  darkTheme: ThemeData(
    colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue, brightness: Brightness.dark),
    useMaterial3: true,
  ),
  themeMode: ThemeMode.system,   // ThemeMode.light / .dark / .system
  home: MyHomePage(),
)
```

### Accessing theme
```dart
final theme = Theme.of(context);
final colorScheme = theme.colorScheme;

colorScheme.primary
colorScheme.secondary
colorScheme.surface
colorScheme.background
colorScheme.error
colorScheme.onPrimary    // text color ON primary
theme.textTheme.bodyMedium
theme.textTheme.titleLarge
```

---

## SafeArea

Prevents widgets from being obscured by system UI (notch, status bar, home indicator).

```dart
SafeArea(
  top: true,
  bottom: true,
  left: false,
  right: false,
  minimum: EdgeInsets.all(8),
  child: Column(children: [...]),
)
```

---

## ClipRRect & ClipOval

### ClipRRect — rounded corners clip
```dart
ClipRRect(
  borderRadius: BorderRadius.circular(16),
  child: Image.network('https://example.com/photo.jpg', fit: BoxFit.cover),
)
```

### ClipOval — circular clip
```dart
ClipOval(
  child: Image.network(
    avatarUrl,
    width: 60,
    height: 60,
    fit: BoxFit.cover,
  ),
)
```

### CircleAvatar (for profile images)
```dart
CircleAvatar(
  radius: 30,
  backgroundImage: NetworkImage(user.avatarUrl),
  backgroundColor: Colors.grey[300],
  onBackgroundImageError: (_, __) {},
  child: user.avatarUrl.isEmpty ? Text(user.initials) : null,
)
```

---

## Opacity & Visibility

```dart
// Opacity - renders but transparent (still takes space)
Opacity(
  opacity: 0.5,   // 0.0 = invisible, 1.0 = fully visible
  child: Text('Semi-transparent'),
)

// Visibility - can hide without taking space
Visibility(
  visible: _isVisible,
  maintainSize: false,     // set true to keep space
  maintainAnimation: false,
  child: Text('Conditional'),
)

// Offstage - hides and removes from layout
Offstage(
  offstage: !_isVisible,
  child: ExpensiveWidget(),
)
```

---

## ListTile

```dart
ListTile(
  leading: CircleAvatar(child: Icon(Icons.person)),
  title: Text('John Doe'),
  subtitle: Text('Software Engineer'),
  trailing: Row(
    mainAxisSize: MainAxisSize.min,
    children: [
      Icon(Icons.star, color: Colors.amber, size: 16),
      Text('4.9'),
      SizedBox(width: 8),
      Icon(Icons.chevron_right),
    ],
  ),
  isThreeLine: false,
  dense: false,
  contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 4),
  selected: _isSelected,
  selectedTileColor: Colors.blue[50],
  tileColor: Colors.white,
  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
  onTap: () {},
  onLongPress: () {},
)
```

---

## PopupMenuButton

```dart
PopupMenuButton<String>(
  icon: Icon(Icons.more_vert),
  tooltip: 'More options',
  offset: Offset(0, 40),  // offset from button
  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
  onSelected: (value) {
    switch (value) {
      case 'edit': _editItem(); break;
      case 'delete': _deleteItem(); break;
    }
  },
  itemBuilder: (context) => [
    PopupMenuItem(
      value: 'edit',
      child: Row(children: [Icon(Icons.edit, size: 18), SizedBox(width: 8), Text('Edit')]),
    ),
    PopupMenuDivider(),
    PopupMenuItem(
      value: 'delete',
      child: Row(children: [
        Icon(Icons.delete, size: 18, color: Colors.red),
        SizedBox(width: 8),
        Text('Delete', style: TextStyle(color: Colors.red)),
      ]),
    ),
  ],
)
```

---

## Spacer

```dart
// Takes up all available space in a Row/Column
Row(
  children: [
    Text('Left'),
    Spacer(),          // pushes right content to the end
    Text('Right'),
  ],
)

// With flex
Row(
  children: [
    Text('Start'),
    Spacer(flex: 2),
    Text('Middle'),
    Spacer(flex: 1),
    Text('End'),
  ],
)
```

---

## TextField Controllers & FocusNodes

```dart
class _MyFormState extends State<MyForm> {
  final _nameController = TextEditingController();
  final _emailController = TextEditingController(text: 'prefilled@example.com');
  final _nameFocus = FocusNode();
  final _emailFocus = FocusNode();

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _nameFocus.dispose();
    _emailFocus.dispose();
    super.dispose();
  }

  void _submit() {
    print(_nameController.text);
    print(_emailController.text);
    _nameController.clear();
  }

  // Move focus to next field
  void _fieldSubmitted() {
    FocusScope.of(context).requestFocus(_emailFocus);
  }
}
```

---

*Last updated: Flutter 3.x / Dart 3.x (null safety)*
