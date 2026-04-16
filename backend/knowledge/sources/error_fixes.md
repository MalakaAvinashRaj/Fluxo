### Error: `Null check operator used on a null value`
**Message:** `Null check operator used on a null value`

**Cause:** Using `!` on a null value at runtime.

```dart
// ❌ BAD
String? name;
print(name!.length);   // crashes if name is null
```

**Fix:**
```dart
// ✅ Option 1: null-aware access
print(name?.length ?? 0);

// ✅ Option 2: guard with if
if (name != null) print(name.length);

// ✅ Option 3: provide default
final length = name?.length ?? 0;

// ✅ Option 4: early return
String getLength(String? value) {
  if (value == null) return 'unknown';
  return '${value.length} chars';
}
```

---

### Error: `LateInitializationError: Field not initialized`
**Message:** `LateInitializationError: Field '_controller' has not been initialized`

**Cause:** `late` variable declared but `initState()` never ran, or was accessed before assignment.

```dart
// ❌ BAD
class _MyState extends State<MyWidget> {
  late TextEditingController _controller;
  // forgot to initialize in initState
}
```

**Fix:**
```dart
// ✅ Initialize in initState
@override
void initState() {
  super.initState();
  _controller = TextEditingController();
}

@override
void dispose() {
  _controller.dispose();
  super.dispose();
}

// ✅ Or use lazy initialization with initializer
late final TextEditingController _controller = TextEditingController();
// ⚠️ But still dispose it in dispose()
```

---

### Error: `The argument type 'String?' can't be assigned to the parameter type 'String'`
**Cause:** Passing nullable to non-nullable parameter.

```dart
// ❌ BAD
String? name = getName();
Text(name)   // Error: String? not assignable to String
```

**Fix:**
```dart
// ✅ Option 1: provide fallback
Text(name ?? 'Unknown')

// ✅ Option 2: assert non-null (use when you're certain)
Text(name!)

// ✅ Option 3: conditional widget
if (name != null) Text(name)

// ✅ Option 4: null coalescing in context
Text(name ?? '')
```

---

### Error: `A value of type 'Null' can't be assigned to a variable of type 'String'`
**Cause:** Trying to assign `null` to a non-nullable variable.

```dart
// ❌ BAD
String name = null;  // compile error
```

**Fix:**
```dart
// ✅ Make nullable
String? name = null;

// ✅ Or provide default
String name = '';

// ✅ Or use late (assign before use)
late String name;
```

---

### Error: `type 'Null' is not a subtype of type 'String'` (runtime)
**Cause:** JSON field is null but model expects non-null.

```dart
// ❌ BAD
factory User.fromJson(Map<String, dynamic> json) => User(
  name: json['name'] as String,   // crashes if 'name' is null/missing in JSON
);
```

**Fix:**
```dart
// ✅ Safe casting with fallback
factory User.fromJson(Map<String, dynamic> json) => User(
  name: (json['name'] as String?) ?? 'Unknown',
  email: json['email']?.toString() ?? '',
  age: (json['age'] as int?) ?? 0,
);
```

---

### Error: `The property 'x' can't be unconditionally accessed because the receiver can be null`
**Cause:** Accessing a member of a nullable object without null check.

```dart
// ❌ BAD
User? user = getUser();
print(user.name);   // compile error
```

**Fix:**
```dart
// ✅ Null-aware access
print(user?.name);
print(user?.name ?? 'No user');

// ✅ Null check with if
if (user != null) {
  print(user.name);   // promoted to non-nullable inside block
}
```

---

## Type Mismatch Errors

---

### Error: `type 'int' is not a subtype of type 'double'`
**Cause:** Dart distinguishes int and double strictly.

```dart
// ❌ BAD
double price = 10;          // compile error (10 is int literal)
Container(width: 100)       // fine in Flutter, but:
double x = someIntValue;    // runtime error if someIntValue is int
```

**Fix:**
```dart
// ✅ Use explicit double literal
double price = 10.0;

// ✅ Convert
double x = someIntValue.toDouble();

// ✅ Cast (when certain of type)
double x = (jsonValue as num).toDouble();

// ✅ In widget properties
Container(width: 100.0, height: 50.0)
// or just use int literals — Flutter accepts num for most
Container(width: 100, height: 50)  // this is fine
```

---

### Error: `type 'List<dynamic>' is not a subtype of type 'List<String>'`
**Cause:** JSON decoding produces `dynamic` types; Dart can't automatically cast.

```dart
// ❌ BAD
final List<String> names = jsonDecode(response.body);  // runtime error
```

**Fix:**
```dart
// ✅ Cast each element
final List<String> names = (jsonDecode(response.body) as List)
    .map((e) => e as String)
    .toList();

// ✅ Or use whereType for safety
final List<String> names = (jsonDecode(response.body) as List)
    .whereType<String>()
    .toList();

// ✅ For complex objects
final List<User> users = (jsonDecode(response.body) as List)
    .map((json) => User.fromJson(json as Map<String, dynamic>))
    .toList();
```

---

### Error: `type '_InternalLinkedHashMap<String, dynamic>' is not a subtype of type 'Map<String, String>'`
**Cause:** JSON maps are `Map<String, dynamic>`, not `Map<String, String>`.

**Fix:**
```dart
// ✅ Use Map<String, dynamic> for JSON
Map<String, dynamic> data = jsonDecode(response.body);

// ✅ If you need Map<String, String>, convert explicitly
Map<String, String> headers = data.map(
  (key, value) => MapEntry(key, value.toString()),
);
```

---

### Error: `A value of type 'Widget Function()' can't be assigned to a variable of type 'Widget'`
**Cause:** Forgetting to call a widget builder function.

```dart
// ❌ BAD
body: buildContent   // forgot ()
```

**Fix:**
```dart
// ✅ Call the function
body: buildContent()

// Or if it's a method:
body: _buildContent()
```

---

### Error: `The operator '[]' isn't defined for the type 'Object'`
**Cause:** Variable typed as `Object` instead of `Map<String, dynamic>`.

```dart
// ❌ BAD
final data = jsonDecode(response.body);  // Object
final name = data['name'];  // error: [] not defined on Object
```

**Fix:**
```dart
// ✅ Cast explicitly
final data = jsonDecode(response.body) as Map<String, dynamic>;
final name = data['name'] as String;
```

---

## Missing Import Errors

---

### Error: `Undefined name 'Colors'`
**Fix:**
```dart
import 'package:flutter/material.dart';
```

---

### Error: `Undefined class 'StatelessWidget'` / `'StatefulWidget'`
**Fix:**
```dart
import 'package:flutter/material.dart';
// or for basic widgets only:
import 'package:flutter/widgets.dart';
```

---

### Error: `Undefined name 'CupertinoIcons'`
**Fix:**
```dart
import 'package:flutter/cupertino.dart';
```

---

### Error: `Undefined name 'File'` / `'Directory'`
**Fix:**
```dart
import 'dart:io';
```

---

### Error: `Undefined name 'jsonDecode'` / `'jsonEncode'`
**Fix:**
```dart
import 'dart:convert';
```

---

### Error: `Undefined name 'Uint8List'` / `'ByteData'`
**Fix:**
```dart
import 'dart:typed_data';
```

---

### Error: `Undefined name 'Timer'`
**Fix:**
```dart
import 'dart:async';
```

---

### Error: `Undefined name 'Platform'`
**Fix:**
```dart
import 'dart:io' show Platform;
```

---

### Error: `Undefined name 'kDebugMode'` / `'kReleaseMode'`
**Fix:**
```dart
import 'package:flutter/foundation.dart';
```

---

### Error: `Undefined name 'compute'`
**Fix:**
```dart
import 'package:flutter/foundation.dart';
```

---

### Error: Target of URI doesn't exist: `'package:my_app/...'`
**Cause:** File doesn't exist, wrong path, or package not in `pubspec.yaml`.

**Fix:**
```bash
# 1. Check file actually exists at the path
# 2. Check pubspec.yaml has the dependency
# 3. Run:
flutter pub get
# 4. For generated files, run:
flutter pub run build_runner build
```

---

## Widget Build Errors

---

### Error: `setState() called after dispose()`
**Message:** `setState() or markNeedsBuild() called after dispose()`

**Cause:** Async callback fires after widget was removed from tree.

**Fix:**
```dart
// ✅ Always check mounted before setState in async functions
Future<void> _fetchData() async {
  final data = await repository.getData();
  if (mounted) {   // ← THE FIX
    setState(() => _data = data);
  }
}
```

---

### Error: `dependOnInheritedWidgetOfExactType<X>() called before build()`
**Cause:** Accessing `BuildContext` in `initState()` for things like `Theme.of`, `Provider.of`.

**Fix:**
```dart
// ❌ BAD
@override
void initState() {
  super.initState();
  final theme = Theme.of(context);  // ERROR: context not ready in initState
}

// ✅ Option 1: use didChangeDependencies
@override
void didChangeDependencies() {
  super.didChangeDependencies();
  final theme = Theme.of(context);  // safe here
}

// ✅ Option 2: use addPostFrameCallback
@override
void initState() {
  super.initState();
  WidgetsBinding.instance.addPostFrameCallback((_) {
    final theme = Theme.of(context);  // safe after first frame
  });
}
```

---

### Error: `Each child must have a unique key` (in lists)
**Cause:** Duplicate or null keys in a list of widgets.

**Fix:**
```dart
// ✅ Use item ID as key
ListView.builder(
  itemBuilder: (_, i) => ItemCard(
    key: ValueKey(items[i].id),
    item: items[i],
  ),
)

// ✅ Or index if no stable ID
key: ValueKey('item_$i')
```

---

### Error: `RenderFlex children have non-zero flex but incoming height/width constraints are unbounded`
**Cause:** Using `Expanded` or `Column` with unbounded constraints (e.g., inside `SingleChildScrollView`).

**Fix:**
```dart
// ❌ BAD — Column inside SingleChildScrollView with Expanded
SingleChildScrollView(
  child: Column(
    children: [
      Expanded(child: Container()),  // ERROR: Column height is unbounded
    ],
  ),
)

// ✅ Option 1: remove Expanded
SingleChildScrollView(
  child: Column(
    children: [
      SizedBox(height: 200, child: Container()),  // fixed height instead
    ],
  ),
)

// ✅ Option 2: use SizedBox with fixed height
SizedBox(
  height: 300,
  child: ListView.builder(...)
)

// ✅ Option 3: use shrinkWrap for ListView inside Column
ListView.builder(
  shrinkWrap: true,
  physics: NeverScrollableScrollPhysics(),  // disable inner scrolling
  itemCount: items.length,
  itemBuilder: (_, i) => ListTile(title: Text(items[i])),
)
```

---

### Error: `Incorrect use of ParentDataWidget`
**Cause:** Using `Expanded` or `Flexible` outside of `Row`/`Column`/`Flex`.

```dart
// ❌ BAD
Container(
  child: Expanded(child: Text('Hello')),  // Expanded not inside Row/Column
)
```

**Fix:**
```dart
// ✅ Wrap with Row or Column
Row(
  children: [
    Expanded(child: Text('Hello')),
  ],
)

// ✅ Or use a different approach
Container(
  width: double.infinity,
  child: Text('Hello'),
)
```

---

### Error: `A build function returned null`
**Cause:** `build()` method missing a return statement in a branch.

```dart
// ❌ BAD
@override
Widget build(BuildContext context) {
  if (_isLoading) {
    return CircularProgressIndicator();
  }
  // forgot to return something for the else case!
}
```

**Fix:**
```dart
// ✅ Always return a widget
@override
Widget build(BuildContext context) {
  if (_isLoading) return Center(child: CircularProgressIndicator());
  return ListView.builder(...);
}
```

---

### Error: `inheritFromWidgetOfExactType` / `dependOnInheritedWidgetOfExactType` returns null
**Cause:** Widget not under the expected InheritedWidget (like `MaterialApp`, `Scaffold`).

```dart
// ❌ BAD — no Scaffold ancestor
Navigator.of(context)  // fails
ScaffoldMessenger.of(context)  // fails
Theme.of(context)  // fails
```

**Fix:**
```dart
// ✅ Make sure widget is inside MaterialApp and Scaffold
class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(  // ← provides Navigator, Theme, etc.
      home: Scaffold(    // ← provides ScaffoldMessenger
        body: MyWidget(), // ← can now access all of the above
      ),
    );
  }
}
```

---

## Layout & Overflow Errors

---

### Error: `BOTTOM OVERFLOWED BY X PIXELS` (Yellow/black stripes)
**Cause:** Child content taller than parent container.

**Fix:**
```dart
// ✅ Option 1: wrap in SingleChildScrollView
body: SingleChildScrollView(
  child: Column(children: [...]),
)

// ✅ Option 2: use Flexible/Expanded to let children shrink
Column(
  children: [
    Expanded(child: ContentWidget()),
    FixedHeightBottomBar(),
  ],
)

// ✅ Option 3: resizeToAvoidBottomInset on Scaffold (keyboard issue)
Scaffold(
  resizeToAvoidBottomInset: true,  // default is true
  body: ...,
)
```

---

### Error: `RIGHT OVERFLOWED BY X PIXELS` in Row
**Fix:**
```dart
// ✅ Option 1: wrap text with Expanded
Row(
  children: [
    Icon(Icons.info),
    Expanded(
      child: Text(
        longText,
        overflow: TextOverflow.ellipsis,
      ),
    ),
  ],
)

// ✅ Option 2: use Flexible
Row(
  children: [
    Icon(Icons.info),
    Flexible(child: Text(longText)),
  ],
)

// ✅ Option 3: use Wrap instead of Row
Wrap(
  children: [Text(word1), Text(word2), Text(word3)],
)
```

---

### Error: `RenderBox was not laid out` / `'size' getter called before layout`
**Cause:** Widget with no parent constraints (placed in a context that gives infinite constraints).

**Fix:**
```dart
// ✅ Give explicit size or wrap in constrained widget
SizedBox(
  width: 200,
  height: 200,
  child: ProblematicWidget(),
)

// Or wrap in Center / Align
Center(child: ProblematicWidget())
```

---

### Error: Overflow in TextField inside Row
```dart
// ❌ BAD
Row(
  children: [
    TextField(),   // TextField needs width constraints
    Text('suffix'),
  ],
)

// ✅ FIX
Row(
  children: [
    Expanded(child: TextField()),
    Text('suffix'),
  ],
)
```

---

## State Management Errors

---

### Error: `Looking up a deactivated widget's ancestor is unsafe`
**Cause:** Using `context` after widget is disposed (often in `async` after `Navigator.pop`).

**Fix:**
```dart
// ✅ Capture what you need BEFORE the async gap
Future<void> _submit() async {
  final navigator = Navigator.of(context);    // capture before await
  final messenger = ScaffoldMessenger.of(context);

  final result = await someAsyncOperation();

  navigator.pop(result);                      // safe to use
  messenger.showSnackBar(SnackBar(content: Text('Done')));
}
```

---

### Error: `Provider.of<X>() called with a context that does not include an X`
**Cause:** Provider not in the widget tree above where you're accessing it.

**Fix:**
```dart
// ✅ Place ChangeNotifierProvider above the widget that uses it
void main() {
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => MyProvider()),
      ],
      child: MaterialApp(home: MyScreen()),
    ),
  );
}

// ✅ Or use ChangeNotifierProvider at the route level
Navigator.push(context,
  MaterialPageRoute(
    builder: (_) => ChangeNotifierProvider(
      create: (_) => DetailProvider(),
      child: DetailScreen(),
    ),
  ),
)
```

---

### Error: `Unhandled Exception: Bad state: Stream has already been listened to`
**Cause:** Using a single-subscription stream with multiple listeners.

**Fix:**
```dart
// ✅ Option 1: Use broadcast stream
final _controller = StreamController<Data>.broadcast();

// ✅ Option 2: Use StreamBuilder (handles subscription internally)
// ✅ Option 3: Cancel existing subscription before creating new one
_subscription?.cancel();
_subscription = stream.listen((data) => setState(() => _data = data));
```

---

### Error: `setState() called during build`
**Cause:** Calling `setState` while the widget is already building.

**Fix:**
```dart
// ❌ BAD
@override
Widget build(BuildContext context) {
  setState(() => _value = 42);  // ERROR: cannot setState during build
  return Text('$_value');
}

// ✅ Use addPostFrameCallback if you need to update after build
@override
void initState() {
  super.initState();
  WidgetsBinding.instance.addPostFrameCallback((_) {
    setState(() => _value = 42);
  });
}
```

---

## Navigation Errors

---

### Error: `Could not find a generator for route RouteSettings(...)`
**Cause:** Named route not defined in `MaterialApp.routes`.

**Fix:**
```dart
// ✅ Define all routes
MaterialApp(
  routes: {
    '/': (context) => HomeScreen(),
    '/detail': (context) => DetailScreen(),  // make sure this matches exactly
  },
  onUnknownRoute: (settings) =>
      MaterialPageRoute(builder: (_) => NotFoundScreen()),
)

// ✅ Or use onGenerateRoute for dynamic routes
onGenerateRoute: (settings) {
  if (settings.name == '/product') {
    return MaterialPageRoute(builder: (_) => ProductScreen());
  }
  return null;
}
```

---

### Error: `Navigator operation requested with a context that includes the Navigator`
**Cause:** Calling `Navigator.of(context)` on the same context that creates the `MaterialApp`.

```dart
// ❌ BAD
class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: ElevatedButton(
        onPressed: () => Navigator.of(context).push(...),  // ERROR
        child: Text('Go'),
      ),
    );
  }
}
```

**Fix:**
```dart
// ✅ Use a separate widget for the content
class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(home: HomeScreen());  // Navigator context is now available inside
  }
}

class HomeScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: () => Navigator.of(context).push(...),  // works
      child: Text('Go'),
    );
  }
}
```

---

### Error: `type 'Null' is not a subtype of type 'X'` when reading route arguments
**Cause:** Route arguments are null or wrong type.

**Fix:**
```dart
// ✅ Safe argument retrieval
final args = ModalRoute.of(context)?.settings.arguments;
if (args == null || args is! MyArgs) {
  // handle missing args
  Navigator.pop(context);
  return;
}
final myArgs = args as MyArgs;
```

---

## Async & Future Errors

---

### Error: `Unhandled Exception: Future already completed`
**Cause:** A `Completer` completed more than once.

**Fix:**
```dart
// ✅ Check before completing
if (!completer.isCompleted) {
  completer.complete(result);
}
```

---

### Error: `Bad state: No element` on Future/Stream
**Cause:** Calling `.first`, `.single`, or similar on empty stream/iterable.

**Fix:**
```dart
// ✅ Use firstOrNull / handle empty
final item = list.isNotEmpty ? list.first : null;

// For streams:
final item = await stream.firstWhere(
  (e) => e.id == targetId,
  orElse: () => defaultValue,
);
```

---

### Error: `Concurrent modification during iteration`
**Cause:** Modifying a list while iterating over it.

**Fix:**
```dart
// ❌ BAD
for (final item in _items) {
  if (item.expired) _items.remove(item);   // modifying while iterating
}

// ✅ Option 1: use removeWhere
_items.removeWhere((item) => item.expired);

// ✅ Option 2: iterate a copy
for (final item in List.from(_items)) {
  if (item.expired) _items.remove(item);
}
```

---

### Error: `TimeoutException` not caught
**Fix:**
```dart
// ✅ Catch TimeoutException specifically
try {
  final result = await operation().timeout(Duration(seconds: 10));
} on TimeoutException {
  setState(() => _error = 'Request timed out');
} on SocketException {
  setState(() => _error = 'No internet connection');
} catch (e) {
  setState(() => _error = 'Unexpected error: $e');
}
```

---

## Platform & Plugin Errors

---

### Error: `MissingPluginException(No implementation found for method...)`
**Cause:** Plugin not properly linked, especially on older versions or after adding a new plugin.

**Fix:**
```bash
# 1. Run flutter pub get
flutter pub get

# 2. For iOS — pod install
cd ios && pod install && cd ..

# 3. Stop the app completely, then run fresh (don't hot reload)
flutter run

# 4. For Android, sometimes needed:
flutter clean
flutter pub get
flutter run

# 5. Check if the plugin supports your platform in pubspec.yaml
```

---

### Error: `Unhandled Exception: PlatformException(channel-error, Unable to establish connection on channel...)`
**Cause:** Method channel not initialized or plugin not configured for the platform.

**Fix:**
```dart
// ✅ Initialize bindings before runApp if using plugins
void main() async {
  WidgetsFlutterBinding.ensureInitialized();   // ← THIS LINE
  // Now safe to call platform plugins:
  await Firebase.initializeApp();
  await SharedPreferences.getInstance();
  runApp(MyApp());
}
```

---

### Error: `setState() or markNeedsBuild() called during build` from platform channel
**Cause:** Platform callback fires on a different isolate/thread and triggers setState on wrong thread.

**Fix:**
```dart
// ✅ Use WidgetsBinding.instance.addPostFrameCallback
platformChannel.setMethodCallHandler((call) async {
  WidgetsBinding.instance.addPostFrameCallback((_) {
    if (mounted) setState(() => _data = call.arguments);
  });
});
```

---

## Build & Compile Errors

---

### Error: `The named parameter 'X' isn't defined`
**Cause:** Typo in property name, or property doesn't exist on that widget.

```dart
// ❌ BAD
Container(colours: Colors.blue)   // typo: should be 'color'
Text('Hi', textsize: 16)          // should be style: TextStyle(fontSize: 16)
```

**Fix:**
- Check widget documentation for correct property name
- Use IDE autocomplete (Ctrl+Space)
- Check Flutter docs / this knowledge base

---

### Error: `Too many positional arguments`
**Cause:** Passing positional args to widget that uses named args.

```dart
// ❌ BAD
Text('Hello', 16)   // fontSize is NOT positional

// ✅ FIX
Text('Hello', style: TextStyle(fontSize: 16))
```

---

### Error: `The method 'X' isn't defined for the class 'Y'`
**Cause:** Wrong type, calling method on wrong object, or method doesn't exist.

**Fix:**
```dart
// Check the type of the object
// Use IDE to see available methods
// Ensure correct import

// Common case: calling List methods on nullable List
List<String>? items;
items.add('value');   // ERROR

// ✅ Fix
items?.add('value');
// or
(items ??= []).add('value');
```

---

### Error: `Getter 'X' is not defined for the class 'Y'`
**Cause:** Accessing a property that doesn't exist, or using wrong type.

```dart
// ❌ BAD
Color color = Colors.blue;
color.value  // fine
color.red    // ERROR: Color doesn't have .red

// ✅ FIX
int red = color.r.round();   // Flutter 3.x uses .r, .g, .b (0.0 to 1.0)
```

---

### Error: `'package:X' is not a valid Dart file import`
**Cause:** Importing a package that isn't in `pubspec.yaml`.

**Fix:**
```yaml
# pubspec.yaml
dependencies:
  http: ^1.2.0
  provider: ^6.1.2
  # add missing package
```
```bash
flutter pub get
```

---

### Error: `The class 'X' doesn't have a constructor named 'Y'`
```dart
// ❌ BAD
ListView.horizontal(...)   // doesn't exist

// ✅ FIX
ListView.builder(
  scrollDirection: Axis.horizontal,
  ...
)
```

---

### Error: `'X' is defined in the libraries 'dart:X' and 'package:X'`
**Cause:** Import conflict — same class name from different packages.

**Fix:**
```dart
// ✅ Use import aliases
import 'dart:io' as io;
import 'package:file_picker/file_picker.dart';

// Then prefix one of them
io.File myFile = io.File(path);
```

---

## Firebase Errors

---

### Error: `[core/no-app] No Firebase App '[DEFAULT]' has been created`
**Fix:**
```dart
// ✅ Ensure Firebase.initializeApp() is called before runApp
void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp(
    options: DefaultFirebaseOptions.currentPlatform,
  );
  runApp(MyApp());
}
```

---

### Error: `Firebase: There is no user record corresponding to this identifier` (auth/user-not-found)
**Fix:**
```dart
try {
  await FirebaseAuth.instance.signInWithEmailAndPassword(
    email: email, password: password,
  );
} on FirebaseAuthException catch (e) {
  switch (e.code) {
    case 'user-not-found':
      showError('No account found for this email');
      break;
    case 'wrong-password':
      showError('Incorrect password');
      break;
    case 'invalid-email':
      showError('Invalid email address');
      break;
    case 'user-disabled':
      showError('This account has been disabled');
      break;
    case 'too-many-requests':
      showError('Too many attempts. Try again later');
      break;
    default:
      showError(e.message ?? 'Authentication failed');
  }
}
```

---

### Error: `cloud_firestore/permission-denied`
**Cause:** Firestore security rules blocking the operation.

**Fix (for development only):**
```
// Firestore rules — allow all for testing
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if request.auth != null;
    }
  }
}
```

---

### Error: `GoogleService-Info.plist not found` (iOS)
**Fix:**
1. Download `GoogleService-Info.plist` from Firebase Console
2. Open Xcode → drag the file into `Runner/` target
3. Make sure "Copy items if needed" is checked
4. Add to target "Runner"

---

### Error: `google-services.json not found` (Android)
**Fix:**
1. Download `google-services.json` from Firebase Console
2. Place it at `android/app/google-services.json`
3. Ensure `android/build.gradle` has `classpath 'com.google.gms:google-services:4.x.x'`
4. Ensure `android/app/build.gradle` has `apply plugin: 'com.google.gms.google-services'`

---

## Dependency & pubspec Errors

---

### Error: `Because X depends on Y >=A <B which doesn't match any versions, version solving failed`
**Cause:** Conflicting dependency versions.

**Fix:**
```bash
# 1. See the full dependency tree
flutter pub deps

# 2. Try to upgrade all packages
flutter pub upgrade

# 3. Override specific conflict (use carefully)
# pubspec.yaml:
dependency_overrides:
  conflicting_package: ^2.0.0

# 4. Check for compatible versions
flutter pub outdated
```

---

### Error: `Git dependencies are not allowed in pub.dev packages`
**Fix:** Use a published version from pub.dev instead of a git dependency where possible, or this is expected when publishing your own package (use pub.dev versions for published packages).

---

### Error: `pubspec.yaml parse error`
**Cause:** Incorrect YAML indentation or syntax.

**Fix:**
```yaml
# ✅ CORRECT pubspec.yaml structure
name: my_app
description: My app.
version: 1.0.0+1

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  http: ^1.2.0           # ← 2 spaces indent, not tabs
  provider: ^6.1.2

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.0

flutter:
  uses-material-design: true
  assets:
    - assets/images/       # ← trailing slash for directory
  fonts:
    - family: Roboto
      fonts:
        - asset: assets/fonts/Roboto-Regular.ttf
```

---

## Release Build Errors

---

### Error: `R8/ProGuard rules missing` — app crashes in release but works in debug
**Cause:** Code obfuscation removes classes that are accessed via reflection (common with JSON serialization, Firebase plugins).

**Fix:**
```
# android/app/proguard-rules.pro
-keep class com.yourpackage.** { *; }
-keep class io.flutter.** { *; }
-dontwarn io.flutter.**

# For Firebase
-keep class com.google.firebase.** { *; }
-keep class com.google.android.gms.** { *; }
```

```groovy
// android/app/build.gradle
buildTypes {
  release {
    minifyEnabled false    // Disable if ProGuard causes issues
    shrinkResources false
    signingConfig signingConfigs.release
  }
}
```

---

### Error: `signingConfig not set` — release build fails
**Fix:**
```groovy
// android/app/build.gradle
android {
  signingConfigs {
    release {
      keyAlias 'your_alias'
      keyPassword 'your_key_pass'
      storeFile file('../keystore.jks')
      storePassword 'your_store_pass'
    }
  }
  buildTypes {
    release {
      signingConfig signingConfigs.release
    }
  }
}
```

---

### Error: `Dart Obfuscation causes stack traces to be unreadable`
**Fix:**
```bash
# Build with obfuscation + save symbols
flutter build apk --obfuscate --split-debug-info=./debug-info

# Deobfuscate a stack trace
flutter symbolize -i crash.txt -d ./debug-info/app.android-arm64.symbols
```

---

## iOS Specific Errors

---

### Error: `CocoaPods not installed` / `pod install failed`
**Fix:**
```bash
# Install CocoaPods
sudo gem install cocoapods

# Or via Homebrew (recommended for M1/M2 Macs)
brew install cocoapods

# Then run:
cd ios
pod install
cd ..
```

---

### Error: `Could not find a simulator` / `No device found`
**Fix:**
```bash
# List available simulators
xcrun simctl list devices

# Open Simulator app
open -a Simulator

# Run on specific simulator
flutter run -d "iPhone 15"
```

---

### Error: `The iOS deployment target 'IPHONEOS_DEPLOYMENT_TARGET' is set to X, but the range of supported deployment target versions is...`
**Fix:**
```ruby
# ios/Podfile — set minimum iOS version at top
platform :ios, '13.0'

# Then:
cd ios && pod install
```

---

### Error: `NSAppTransportSecurity` — network requests blocked on iOS
**Fix:**
```xml
<!-- ios/Runner/Info.plist -->
<key>NSAppTransportSecurity</key>
<dict>
  <key>NSAllowsArbitraryLoads</key>
  <true/>
</dict>
```
> ⚠️ Only for development. For production, configure specific domains.

---

### Error: Permission denied — camera, location, photos (iOS)
**Fix:**
```xml
<!-- ios/Runner/Info.plist -->
<key>NSCameraUsageDescription</key>
<string>This app needs camera access to take photos.</string>

<key>NSPhotoLibraryUsageDescription</key>
<string>This app needs access to your photo library.</string>

<key>NSLocationWhenInUseUsageDescription</key>
<string>This app needs location access to show nearby places.</string>

<key>NSMicrophoneUsageDescription</key>
<string>This app needs microphone access for audio recording.</string>
```

---

## Android Specific Errors

---

### Error: `Manifest merger failed — uses-sdk:minSdkVersion X cannot be smaller than version Y declared in library`
**Fix:**
```groovy
// android/app/build.gradle
android {
  defaultConfig {
    minSdkVersion 21   // bump to match required minimum
    targetSdkVersion 34
    compileSdkVersion 34
  }
}
```

---

### Error: `Execution failed for task ':app:processDebugGoogleServices'`
**Fix:**
1. Ensure `google-services.json` is at `android/app/google-services.json`
2. Ensure plugin applied in `android/app/build.gradle`:
```groovy
apply plugin: 'com.google.gms.google-services'
```

---

### Error: Permission denied — camera, storage, location (Android)
**Fix:**
```xml
<!-- android/app/src/main/AndroidManifest.xml -->
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE"
    android:maxSdkVersion="29" />
<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.RECORD_AUDIO" />
```

```dart
// Request at runtime with permission_handler package
import 'package:permission_handler/permission_handler.dart';

final status = await Permission.camera.request();
if (status.isGranted) {
  // proceed
} else if (status.isPermanentlyDenied) {
  openAppSettings();
}
```

---

### Error: `Cleartext HTTP traffic not permitted` (Android 9+)
**Fix:**
```xml
<!-- android/app/src/main/AndroidManifest.xml -->
<application
  android:usesCleartextTraffic="true"  <!-- allow HTTP (not HTTPS) -->
  ...>
```

---

### Error: `MultiDex not enabled` — method count exceeds 65,536
**Fix:**
```groovy
// android/app/build.gradle
android {
  defaultConfig {
    multiDexEnabled true
  }
}
dependencies {
  implementation 'androidx.multidex:multidex:2.0.1'
}
```

---

## Performance Issues

---

### Issue: Jank / dropped frames — `build()` called too often

**Diagnosis:**
```dart
// Add this in debug mode to see rebuilds
// Install Flutter DevTools: flutter pub global activate devtools
```

**Fix:**
```dart
// ✅ Use const constructors
const Text('Static text')
const SizedBox(height: 16)
const EdgeInsets.all(16)

// ✅ Extract static parts to separate StatelessWidgets
// ✅ Use Provider.select instead of watch for partial state
final count = context.select<CartProvider, int>((c) => c.itemCount);

// ✅ Use RepaintBoundary for complex isolated widgets
RepaintBoundary(child: ExpensiveChartWidget())

// ✅ Use AutomaticKeepAliveClientMixin for Tab/PageView items
class _MyTabState extends State<MyTab> with AutomaticKeepAliveClientMixin {
  @override
  bool get wantKeepAlive => true;

  @override
  Widget build(BuildContext context) {
    super.build(context);  // REQUIRED
    return ExpensiveWidget();
  }
}
```

---

### Issue: Images consuming too much memory
**Fix:**
```dart
// ✅ Set cacheWidth / cacheHeight to decode at smaller resolution
Image.network(
  url,
  cacheWidth: 300,    // decode to 300px wide (saves memory)
  cacheHeight: 300,
)

// ✅ Use cached_network_image package for HTTP caching
import 'package:cached_network_image/cached_network_image.dart';

CachedNetworkImage(
  imageUrl: url,
  placeholder: (_, __) => CircularProgressIndicator(),
  errorWidget: (_, __, ___) => Icon(Icons.error),
  memCacheWidth: 300,
)
```

---

## Image & Asset Errors

---

### Error: `Unable to load asset: assets/images/logo.png`
**Fix:**
```yaml
# pubspec.yaml — declare the asset
flutter:
  assets:
    - assets/images/logo.png    # specific file
    - assets/images/            # entire directory (trailing slash required)
    - assets/                   # all assets recursively
```
```bash
# Ensure the file exists at the exact path
# Then:
flutter pub get
```

---

### Error: `Asset manifest is empty` / assets not loading after adding
**Fix:**
```bash
flutter clean
flutter pub get
flutter run
```

---

## Font & Text Errors

---

### Error: Custom font not showing
**Fix:**
```yaml
# pubspec.yaml — declare fonts
flutter:
  fonts:
    - family: MyFont
      fonts:
        - asset: assets/fonts/MyFont-Regular.ttf
          weight: 400
        - asset: assets/fonts/MyFont-Bold.ttf
          weight: 700
        - asset: assets/fonts/MyFont-Italic.ttf
          style: italic
```

```dart
// Apply globally
ThemeData(
  fontFamily: 'MyFont',
)

// Apply locally
Text('Hello', style: TextStyle(fontFamily: 'MyFont'))
```

---

## Keyboard & Focus Errors

---

### Issue: Keyboard overlaps content / TextField not visible when keyboard opens
**Fix:**
```dart
// ✅ Option 1: resizeToAvoidBottomInset (default true on Scaffold)
Scaffold(
  resizeToAvoidBottomInset: true,
  body: SingleChildScrollView(
    child: Column(children: [...]),
  ),
)

// ✅ Option 2: scroll to focused field
ScrollController _scrollController = ScrollController();
FocusNode _fieldFocus = FocusNode();

_fieldFocus.addListener(() {
  if (_fieldFocus.hasFocus) {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      Scrollable.ensureVisible(
        _fieldFocus.context!,
        duration: Duration(milliseconds: 300),
      );
    });
  }
});
```

---

### Issue: Keyboard doesn't dismiss on tap outside TextField
**Fix:**
```dart
// ✅ Wrap Scaffold body with GestureDetector
GestureDetector(
  onTap: () => FocusScope.of(context).unfocus(),
  child: Scaffold(
    body: ...,
  ),
)
```

---

## Testing Errors

---

### Error: `No MediaQuery widget found`
**Cause:** Widget under test not wrapped in MaterialApp.

**Fix:**
```dart
testWidgets('my widget test', (tester) async {
  await tester.pumpWidget(
    MaterialApp(           // ← wraps with all needed ancestors
      home: MyWidget(),
    ),
  );
  // test code...
});
```

---

### Error: `A Timer is still pending` after test
**Fix:**
```dart
testWidgets('...', (tester) async {
  await tester.pumpWidget(MyWidget());
  await tester.pump();                // process one frame
  await tester.pumpAndSettle();      // wait for all animations to finish
  // or
  await tester.pump(Duration(seconds: 3));  // advance by specific duration
});
```

---

### Error: `Null check operator used on a null value` in tests (finding widgets)
**Cause:** `find.byType(X).evaluate().first` returns null.

**Fix:**
```dart
// ✅ Use findsOneWidget / findsWidgets matchers
expect(find.byType(TextField), findsOneWidget);
expect(find.text('Hello'), findsWidgets);
expect(find.byKey(Key('submit')), findsNothing);

// ✅ Or check before accessing
final finder = find.byType(TextField);
if (tester.any(finder)) {
  await tester.tap(finder);
}
```

---

## Quick Reference: Most Common Fixes

| Error | Quick Fix |
|-------|-----------|
| `Null check on null value` | Use `?.` or `?? default` instead of `!` |
| `setState after dispose` | Check `if (mounted)` before setState in async |
| `OVERFLOWED BY X pixels` | Wrap in `SingleChildScrollView` or use `Expanded` |
| `Expanded outside Row/Column` | Move `Expanded` into a `Row` or `Column` |
| `No implementation found for method` | `flutter clean && flutter pub get && pod install` |
| `No MediaQuery found` | Wrap in `MaterialApp` |
| `No Firebase App` | Call `WidgetsFlutterBinding.ensureInitialized()` + `Firebase.initializeApp()` before `runApp` |
| `Asset not found` | Add to `pubspec.yaml` flutter.assets, run `flutter pub get` |
| `Type cast fails` | Use `as Type?` and null-check, or `is Type` guard |
| `Missing plugin` | Run `flutter clean`, `flutter pub get`, restart app (no hot reload) |
| `Provider not found` | Place `ChangeNotifierProvider` higher in the widget tree |
| `Context in initState` | Use `didChangeDependencies` or `addPostFrameCallback` |

---

*Last updated: Flutter 3.x / Dart 3.x (null safety)*
