## PageView & PageController

Swipeable pages — used for onboarding flows, carousels, and tab-like screens.

### Constructor
```dart
PageView({
  Key? key,
  Axis scrollDirection = Axis.horizontal,
  bool reverse = false,
  PageController? controller,
  ScrollPhysics? physics,
  bool pageSnapping = true,
  ValueChanged<int>? onPageChanged,
  bool padEnds = true,
  List<Widget> children = const [],
})

PageView.builder({
  required int? itemCount,
  required IndexedWidgetBuilder itemBuilder,
  PageController? controller,
  ValueChanged<int>? onPageChanged,
  bool pageSnapping = true,
  ScrollPhysics? physics,
  Axis scrollDirection = Axis.horizontal,
  bool reverse = false,
  bool padEnds = true,
})
```

### PageController
```dart
PageController({
  int initialPage = 0,
  bool keepPage = true,
  double viewportFraction = 1.0,  // < 1.0 shows adjacent pages (carousel)
})

// Methods
controller.animateToPage(index, duration: Duration(ms: 300), curve: Curves.ease)
controller.jumpToPage(index)
controller.nextPage(duration: Duration(milliseconds: 300), curve: Curves.ease)
controller.previousPage(duration: Duration(milliseconds: 300), curve: Curves.ease)
controller.page     // current page as double (0.0, 1.0, etc.)
```

### Full Example — Onboarding
```dart
class OnboardingScreen extends StatefulWidget {
  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final _controller = PageController();
  int _currentPage = 0;

  final _pages = [
    OnboardPage(title: 'Welcome', icon: Icons.waving_hand),
    OnboardPage(title: 'Discover', icon: Icons.explore),
    OnboardPage(title: 'Get Started', icon: Icons.rocket_launch),
  ];

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Column(
        children: [
          Expanded(
            child: PageView.builder(
              controller: _controller,
              itemCount: _pages.length,
              onPageChanged: (i) => setState(() => _currentPage = i),
              itemBuilder: (context, i) => _pages[i],
            ),
          ),
          // Dot indicators
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: List.generate(_pages.length, (i) {
              return AnimatedContainer(
                duration: Duration(milliseconds: 300),
                margin: EdgeInsets.symmetric(horizontal: 4),
                width: _currentPage == i ? 24 : 8,
                height: 8,
                decoration: BoxDecoration(
                  color: _currentPage == i ? Colors.blue : Colors.grey[300],
                  borderRadius: BorderRadius.circular(4),
                ),
              );
            }),
          ),
          SizedBox(height: 16),
          // Next / Done button
          Padding(
            padding: EdgeInsets.all(24),
            child: ElevatedButton(
              onPressed: () {
                if (_currentPage < _pages.length - 1) {
                  _controller.nextPage(
                    duration: Duration(milliseconds: 300),
                    curve: Curves.easeInOut,
                  );
                } else {
                  Navigator.pushReplacementNamed(context, '/home');
                }
              },
              style: ElevatedButton.styleFrom(minimumSize: Size.fromHeight(48)),
              child: Text(_currentPage < _pages.length - 1 ? 'Next' : 'Get Started'),
            ),
          ),
        ],
      ),
    );
  }
}
```

### Carousel (viewportFraction)
```dart
PageView.builder(
  controller: PageController(viewportFraction: 0.85),   // shows 85% of each page
  itemCount: items.length,
  itemBuilder: (context, index) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        double value = 1.0;
        if (_controller.position.haveDimensions) {
          value = _controller.page! - index;
          value = (1 - (value.abs() * 0.3)).clamp(0.0, 1.0);
        }
        return Transform.scale(scale: value, child: child);
      },
      child: Card(
        margin: EdgeInsets.symmetric(horizontal: 8, vertical: 16),
        child: Container(color: Colors.primaries[index % Colors.primaries.length]),
      ),
    );
  },
)
```

---

## CustomScrollView & Slivers

Combine multiple scrollable pieces with different behaviors in one scroll.

```dart
CustomScrollView(
  slivers: [
    SliverAppBar(...),
    SliverToBoxAdapter(child: HeaderWidget()),
    SliverPadding(
      padding: EdgeInsets.all(16),
      sliver: SliverGrid(
        delegate: SliverChildBuilderDelegate(
          (_, i) => Card(child: Text('$i')),
          childCount: 6,
        ),
        gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(crossAxisCount: 2),
      ),
    ),
    SliverList(
      delegate: SliverChildBuilderDelegate(
        (_, i) => ListTile(title: Text('Item $i')),
        childCount: 20,
      ),
    ),
    SliverFillRemaining(
      hasScrollBody: false,
      child: Center(child: Text('End of content')),
    ),
  ],
)
```

### Sliver Types

| Widget | Description |
|--------|-------------|
| `SliverList` | Lazy vertical list inside CustomScrollView |
| `SliverGrid` | Lazy grid inside CustomScrollView |
| `SliverToBoxAdapter` | Wraps a normal (box) widget for use in slivers |
| `SliverPadding` | Adds padding around a sliver |
| `SliverAppBar` | Collapsible/floating app bar |
| `SliverFillRemaining` | Fills remaining space in the scroll view |
| `SliverFixedExtentList` | List where every item has the same height (more efficient) |
| `SliverPrototypeExtentList` | List where height is derived from a prototype widget |
| `SliverOpacity` | Applies opacity to a sliver |
| `SliverAnimatedList` | Animated version of SliverList |
| `SliverCrossAxisGroup` | Places slivers side by side (Flutter 3.x) |

---

## SliverAppBar

Collapsible app bar that integrates with `CustomScrollView`.

```dart
SliverAppBar(
  // Core behavior
  floating: true,           // reappears when scrolling up even partially
  pinned: true,             // always visible at top when collapsed
  snap: true,               // snap to fully shown/hidden (requires floating: true)
  stretch: true,            // stretches when over-scrolled

  // Sizing
  expandedHeight: 200.0,    // height when fully expanded
  collapsedHeight: kToolbarHeight,  // height when collapsed (default: toolbar height)
  toolbarHeight: kToolbarHeight,

  // Content
  title: Text('My App'),
  centerTitle: false,
  leading: IconButton(icon: Icon(Icons.menu), onPressed: () {}),
  actions: [IconButton(icon: Icon(Icons.search), onPressed: () {})],

  // Flexible space (background, parallax)
  flexibleSpace: FlexibleSpaceBar(
    title: Text('Title'),
    centerTitle: true,
    background: Image.asset('assets/header.jpg', fit: BoxFit.cover),
    collapseMode: CollapseMode.parallax,  // parallax, pin, none
    stretchModes: [StretchMode.zoomBackground, StretchMode.blurBackground],
  ),

  // Styling
  backgroundColor: Colors.transparent,
  foregroundColor: Colors.white,
  elevation: 0,
  scrolledUnderElevation: 4,
  shadowColor: Colors.black26,
  surfaceTintColor: Colors.transparent,
  forceElevated: false,

  // Tab bar at bottom
  bottom: TabBar(tabs: [Tab(text: 'A'), Tab(text: 'B')]),
  bottomOpacity: 1.0,
)
```

---

## SliverPersistentHeader

Custom sticky header with dynamic height.

```dart
class _MyStickyHeader extends SliverPersistentHeaderDelegate {
  final String title;
  _MyStickyHeader(this.title);

  @override
  double get minExtent => 48;
  @override
  double get maxExtent => 120;

  @override
  Widget build(BuildContext context, double shrinkOffset, bool overlapsContent) {
    final progress = shrinkOffset / maxExtent;  // 0.0 = expanded, 1.0 = collapsed
    return Container(
      color: Color.lerp(Colors.transparent, Colors.blue, progress),
      child: Align(
        alignment: Alignment.bottomLeft,
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Text(
            title,
            style: TextStyle(
              fontSize: lerpDouble(24, 16, progress)!,
              color: Colors.white,
              fontWeight: FontWeight.bold,
            ),
          ),
        ),
      ),
    );
  }

  @override
  bool shouldRebuild(_MyStickyHeader oldDelegate) => oldDelegate.title != title;
}

// Usage in CustomScrollView
SliverPersistentHeader(
  pinned: true,
  floating: false,
  delegate: _MyStickyHeader('Section Title'),
),
```

---

## NestedScrollView

Two scroll controllers — outer for the header, inner for the body (e.g., TabBarView).

```dart
NestedScrollView(
  headerSliverBuilder: (context, innerBoxIsScrolled) => [
    SliverAppBar(
      title: Text('Profile'),
      pinned: true,
      floating: false,
      expandedHeight: 200,
      flexibleSpace: FlexibleSpaceBar(
        background: UserProfileHeader(),
      ),
      forceElevated: innerBoxIsScrolled,
      bottom: TabBar(
        controller: _tabController,
        tabs: [Tab(text: 'Posts'), Tab(text: 'Likes')],
      ),
    ),
  ],
  body: TabBarView(
    controller: _tabController,
    children: [
      PostsList(),
      LikesList(),
    ],
  ),
)
```

---

## ExpansionTile & ExpansionPanel

### ExpansionTile
```dart
ExpansionTile(
  leading: Icon(Icons.settings),
  title: Text('Advanced Settings'),
  subtitle: Text('Configure advanced options'),
  trailing: null,   // null = default arrow; provide widget to customize
  initiallyExpanded: false,
  maintainState: true,   // keep expanded child in tree when collapsed
  expansionAnimationStyle: AnimationStyle(
    curve: Curves.easeInOut,
    duration: Duration(milliseconds: 300),
  ),
  tilePadding: EdgeInsets.symmetric(horizontal: 16),
  childrenPadding: EdgeInsets.all(16),
  backgroundColor: Colors.blue[50],
  collapsedBackgroundColor: Colors.white,
  iconColor: Colors.blue,
  collapsedIconColor: Colors.grey,
  textColor: Colors.blue,
  collapsedTextColor: Colors.black87,
  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
  onExpansionChanged: (expanded) => print('Expanded: $expanded'),
  children: [
    SwitchListTile(title: Text('Option A'), value: _optA, onChanged: (v) => setState(() => _optA = v)),
    SwitchListTile(title: Text('Option B'), value: _optB, onChanged: (v) => setState(() => _optB = v)),
  ],
)
```

### Programmatic control
```dart
// Use ExpansionTileController (Flutter 3.4+)
final _tileController = ExpansionTileController();

ExpansionTile(
  controller: _tileController,
  title: Text('Controlled Tile'),
  children: [...],
)

// Control externally
_tileController.expand()
_tileController.collapse()
_tileController.isExpanded   // bool
```

### ExpansionPanelList
```dart
ExpansionPanelList(
  elevation: 1,
  expandedHeaderPadding: EdgeInsets.zero,
  dividerColor: Colors.grey[300],
  expansionCallback: (index, isExpanded) {
    setState(() => _items[index].isExpanded = !isExpanded);
  },
  children: _items.map((item) => ExpansionPanel(
    isExpanded: item.isExpanded,
    canTapOnHeader: true,
    headerBuilder: (context, isExpanded) => ListTile(
      title: Text(item.title),
    ),
    body: Padding(
      padding: EdgeInsets.all(16),
      child: Text(item.body),
    ),
  )).toList(),
)

// Radio variant — only one open at a time
ExpansionPanelList.radio(
  expansionCallback: (index, isExpanded) {},
  children: _items.map((item) => ExpansionPanelRadio(
    value: item.id,
    headerBuilder: (context, isExpanded) => ListTile(title: Text(item.title)),
    body: Text(item.body),
  )).toList(),
)
```

---

## Stepper

Step-by-step flow widget.

```dart
Stepper(
  currentStep: _currentStep,
  type: StepperType.vertical,   // vertical, horizontal
  physics: ClampingScrollPhysics(),
  onStepTapped: (step) => setState(() => _currentStep = step),
  onStepContinue: () {
    if (_currentStep < _steps.length - 1) {
      setState(() => _currentStep++);
    } else {
      _submit();
    }
  },
  onStepCancel: () {
    if (_currentStep > 0) setState(() => _currentStep--);
  },
  controlsBuilder: (context, details) {
    return Row(
      children: [
        ElevatedButton(
          onPressed: details.onStepContinue,
          child: Text(_currentStep < _steps.length - 1 ? 'Continue' : 'Submit'),
        ),
        SizedBox(width: 8),
        if (_currentStep > 0)
          TextButton(onPressed: details.onStepCancel, child: Text('Back')),
      ],
    );
  },
  steps: [
    Step(
      title: Text('Account'),
      subtitle: Text('Basic information'),
      isActive: _currentStep >= 0,
      state: _currentStep > 0 ? StepState.complete : StepState.indexed,
      content: AccountForm(),
    ),
    Step(
      title: Text('Profile'),
      isActive: _currentStep >= 1,
      state: _currentStep > 1 ? StepState.complete : StepState.indexed,
      content: ProfileForm(),
    ),
    Step(
      title: Text('Review'),
      isActive: _currentStep >= 2,
      state: StepState.indexed,
      content: ReviewScreen(),
    ),
  ],
)
```

### StepState Values
- `indexed` — shows step number
- `editing` — pencil icon
- `complete` — checkmark
- `disabled` — grayed out
- `error` — error icon

---

## DataTable

```dart
DataTable(
  sortColumnIndex: _sortColumn,
  sortAscending: _sortAscending,
  headingRowColor: MaterialStateProperty.all(Colors.grey[200]),
  headingTextStyle: TextStyle(fontWeight: FontWeight.bold, color: Colors.black87),
  dataRowMinHeight: 40,
  dataRowMaxHeight: 60,
  dataTextStyle: TextStyle(fontSize: 14),
  dividerThickness: 1,
  showCheckboxColumn: true,
  onSelectAll: (selected) {
    setState(() => _rows.forEach((r) => r.selected = selected ?? false));
  },
  columns: [
    DataColumn(
      label: Text('Name'),
      onSort: (columnIndex, ascending) {
        setState(() {
          _sortColumn = columnIndex;
          _sortAscending = ascending;
          _rows.sort((a, b) => ascending
              ? a.name.compareTo(b.name)
              : b.name.compareTo(a.name));
        });
      },
    ),
    DataColumn(label: Text('Age'), numeric: true),
    DataColumn(label: Text('Role')),
  ],
  rows: _rows.map((row) => DataRow(
    selected: row.selected,
    onSelectChanged: (selected) => setState(() => row.selected = selected ?? false),
    color: MaterialStateProperty.resolveWith<Color?>((states) {
      if (states.contains(MaterialState.selected)) return Colors.blue[50];
      return null;
    }),
    cells: [
      DataCell(Text(row.name)),
      DataCell(Text('${row.age}')),
      DataCell(
        Chip(label: Text(row.role)),
        showEditIcon: true,
        onTap: () => _editRole(row),
      ),
    ],
  )).toList(),
)
```

### PaginatedDataTable
```dart
PaginatedDataTable(
  header: Text('Users'),
  rowsPerPage: 10,
  availableRowsPerPage: [5, 10, 25],
  onRowsPerPageChanged: (rows) => setState(() => _rowsPerPage = rows!),
  sortColumnIndex: _sortColumn,
  sortAscending: _sortAscending,
  actions: [
    IconButton(icon: Icon(Icons.filter_list), onPressed: _filter),
    IconButton(icon: Icon(Icons.refresh), onPressed: _refresh),
  ],
  columns: [...],
  source: MyDataTableSource(),   // extend DataTableSource
)

// DataTableSource
class MyDataTableSource extends DataTableSource {
  @override
  DataRow? getRow(int index) {
    if (index >= _data.length) return null;
    final item = _data[index];
    return DataRow(cells: [DataCell(Text(item.name))]);
  }

  @override
  bool get isRowCountApproximate => false;
  @override
  int get rowCount => _data.length;
  @override
  int get selectedRowCount => _selected;
}
```

---

## Table

Low-level table with fine-grained column width control.

```dart
Table(
  defaultVerticalAlignment: TableCellVerticalAlignment.middle,
  border: TableBorder.all(color: Colors.grey[300]!, width: 1),
  columnWidths: {
    0: FixedColumnWidth(120),    // fixed px
    1: FlexColumnWidth(2),       // flex ratio
    2: FlexColumnWidth(1),
    3: IntrinsicColumnWidth(),   // size to content
    4: FractionColumnWidth(0.2), // % of table width
  },
  children: [
    // Header row
    TableRow(
      decoration: BoxDecoration(color: Colors.grey[200]),
      children: ['Name', 'Category', 'Price', 'Stock', 'Action']
          .map((h) => Padding(
                padding: EdgeInsets.all(8),
                child: Text(h, style: TextStyle(fontWeight: FontWeight.bold)),
              ))
          .toList(),
    ),
    // Data rows
    ...products.map((p) => TableRow(children: [
      TableCell(
        verticalAlignment: TableCellVerticalAlignment.top,
        child: Padding(padding: EdgeInsets.all(8), child: Text(p.name)),
      ),
      Padding(padding: EdgeInsets.all(8), child: Text(p.category)),
      Padding(padding: EdgeInsets.all(8), child: Text('\$${p.price}')),
      Padding(padding: EdgeInsets.all(8), child: Text('${p.stock}')),
      IconButton(icon: Icon(Icons.edit, size: 18), onPressed: () => _edit(p)),
    ])),
  ],
)
```

---

## Chip Variants

### ActionChip — tappable, triggers an action
```dart
ActionChip(
  avatar: Icon(Icons.star, size: 18),
  label: Text('Favorite'),
  onPressed: () => _addToFavorites(),
  backgroundColor: Colors.amber[50],
  side: BorderSide(color: Colors.amber),
  shape: StadiumBorder(),
  elevation: 2,
  pressElevation: 4,
)
```

### FilterChip — toggleable on/off for filters
```dart
FilterChip(
  label: Text('Flutter'),
  selected: _filters.contains('flutter'),
  onSelected: (selected) {
    setState(() {
      selected ? _filters.add('flutter') : _filters.remove('flutter');
    });
  },
  selectedColor: Colors.blue[100],
  checkmarkColor: Colors.blue,
  avatar: Icon(Icons.code, size: 16),
  showCheckmark: true,
)

// Wrap of FilterChips
Wrap(
  spacing: 8,
  children: tags.map((tag) => FilterChip(
    label: Text(tag),
    selected: _selectedTags.contains(tag),
    onSelected: (v) => setState(() => v ? _selectedTags.add(tag) : _selectedTags.remove(tag)),
  )).toList(),
)
```

### ChoiceChip — single selection from group (like radio)
```dart
Wrap(
  spacing: 8,
  children: sizes.map((size) => ChoiceChip(
    label: Text(size),
    selected: _selectedSize == size,
    onSelected: (selected) {
      if (selected) setState(() => _selectedSize = size);
    },
    selectedColor: Colors.blue,
    labelStyle: TextStyle(
      color: _selectedSize == size ? Colors.white : Colors.black,
    ),
  )).toList(),
)
```

### InputChip — deletable tag/chip
```dart
InputChip(
  label: Text(tag),
  avatar: CircleAvatar(child: Text(tag[0].toUpperCase())),
  onDeleted: () => setState(() => _tags.remove(tag)),
  deleteIcon: Icon(Icons.close, size: 16),
  deleteIconColor: Colors.grey[600],
  onPressed: () => _showTagDetails(tag),
  selected: _selectedTags.contains(tag),
  materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
)
```

### Chip (basic display-only)
```dart
Chip(
  label: Text('New'),
  avatar: Icon(Icons.fiber_new, size: 18, color: Colors.green),
  backgroundColor: Colors.green[50],
  side: BorderSide(color: Colors.green),
  onDeleted: () {},   // makes it deletable; omit for display-only
  padding: EdgeInsets.symmetric(horizontal: 4),
  labelPadding: EdgeInsets.only(left: 4),
  visualDensity: VisualDensity.compact,
)
```

---

## Autocomplete

```dart
// Basic Autocomplete
Autocomplete<String>(
  optionsBuilder: (TextEditingValue textEditingValue) {
    if (textEditingValue.text.isEmpty) return const Iterable<String>.empty();
    return _allOptions.where((option) =>
        option.toLowerCase().contains(textEditingValue.text.toLowerCase()));
  },
  onSelected: (String selection) {
    setState(() => _selectedCity = selection);
  },
  fieldViewBuilder: (context, controller, focusNode, onFieldSubmitted) {
    return TextField(
      controller: controller,
      focusNode: focusNode,
      decoration: InputDecoration(
        labelText: 'City',
        border: OutlineInputBorder(),
      ),
    );
  },
  optionsViewBuilder: (context, onSelected, options) {
    return Align(
      alignment: Alignment.topLeft,
      child: Material(
        elevation: 4,
        borderRadius: BorderRadius.circular(8),
        child: ConstrainedBox(
          constraints: BoxConstraints(maxHeight: 200),
          child: ListView.builder(
            shrinkWrap: true,
            itemCount: options.length,
            itemBuilder: (_, i) {
              final option = options.elementAt(i);
              return ListTile(
                title: Text(option),
                onTap: () => onSelected(option),
              );
            },
          ),
        ),
      ),
    );
  },
)

// Async options (API search)
Autocomplete<User>(
  optionsBuilder: (textEditingValue) async* {
    if (textEditingValue.text.length < 2) return;
    final users = await ApiService.searchUsers(textEditingValue.text);
    yield* Stream.value(users);
  },
  displayStringForOption: (user) => user.name,
  onSelected: (user) => setState(() => _selectedUser = user),
)
```

---

## DatePicker & TimePicker

### DatePicker
```dart
Future<void> _selectDate() async {
  final picked = await showDatePicker(
    context: context,
    initialDate: _selectedDate ?? DateTime.now(),
    firstDate: DateTime(2000),
    lastDate: DateTime(2100),
    initialEntryMode: DatePickerEntryMode.calendar,  // or .input
    initialDatePickerMode: DatePickerMode.day,        // or .year
    helpText: 'Select Date',
    cancelText: 'Cancel',
    confirmText: 'OK',
    fieldLabelText: 'Enter Date',
    fieldHintText: 'MM/DD/YYYY',
    locale: Locale('en', 'US'),
    selectableDayPredicate: (date) {
      // disable weekends
      return date.weekday != DateTime.saturday && date.weekday != DateTime.sunday;
    },
    builder: (context, child) {
      // Custom theme
      return Theme(
        data: Theme.of(context).copyWith(
          colorScheme: ColorScheme.light(
            primary: Colors.blue,
            onPrimary: Colors.white,
            surface: Colors.white,
          ),
        ),
        child: child!,
      );
    },
  );
  if (picked != null) setState(() => _selectedDate = picked);
}
```

### DateRangePicker
```dart
Future<void> _selectDateRange() async {
  final picked = await showDateRangePicker(
    context: context,
    firstDate: DateTime.now(),
    lastDate: DateTime.now().add(Duration(days: 365)),
    initialDateRange: _dateRange,
    helpText: 'Select Stay Dates',
    saveText: 'Done',
  );
  if (picked != null) setState(() => _dateRange = picked);
}

// picked is DateTimeRange
print(_dateRange.start);
print(_dateRange.end);
print(_dateRange.duration);  // Duration
```

### TimePicker
```dart
Future<void> _selectTime() async {
  final picked = await showTimePicker(
    context: context,
    initialTime: _selectedTime ?? TimeOfDay.now(),
    initialEntryMode: TimePickerEntryMode.dial,   // or .input
    helpText: 'Select Time',
    cancelText: 'Cancel',
    confirmText: 'OK',
    hourLabelText: 'Hour',
    minuteLabelText: 'Minute',
    use24HourFormat: false,   // not direct prop, depends on locale
    builder: (context, child) => MediaQuery(
      data: MediaQuery.of(context).copyWith(alwaysUse24HourFormat: true),
      child: child!,
    ),
  );
  if (picked != null) setState(() => _selectedTime = picked);
}

// TimeOfDay
TimeOfDay(hour: 14, minute: 30)
_selectedTime.format(context)  // "2:30 PM" or "14:30" based on locale
_selectedTime.hour
_selectedTime.minute
```

---

## Tooltip

```dart
Tooltip(
  message: 'This is a helpful tooltip',
  preferBelow: true,          // show below the widget
  verticalOffset: 24,         // distance from widget
  padding: EdgeInsets.symmetric(horizontal: 12, vertical: 6),
  margin: EdgeInsets.all(8),
  decoration: BoxDecoration(
    color: Colors.black87,
    borderRadius: BorderRadius.circular(6),
  ),
  textStyle: TextStyle(color: Colors.white, fontSize: 12),
  waitDuration: Duration(milliseconds: 500),  // delay before showing
  showDuration: Duration(seconds: 2),         // how long to stay
  triggerMode: TooltipTriggerMode.tap,        // tap, longPress (default)
  child: IconButton(
    icon: Icon(Icons.help_outline),
    onPressed: null,
  ),
)

// Rich tooltip (Flutter 3.x)
Tooltip(
  richMessage: TextSpan(children: [
    TextSpan(text: 'Bold ', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white)),
    TextSpan(text: 'and normal', style: TextStyle(color: Colors.white70)),
  ]),
  child: Icon(Icons.info),
)
```

---

## Badge

Material 3 badge widget (Flutter 3.10+).

```dart
// On an icon
Badge(
  label: Text('3'),
  backgroundColor: Colors.red,
  textColor: Colors.white,
  isLabelVisible: _unreadCount > 0,
  offset: Offset(6, -6),   // position relative to child
  child: Icon(Icons.notifications),
)

// Small dot badge (no label)
Badge(
  isLabelVisible: _hasUpdates,
  child: Icon(Icons.inbox),
)

// In BottomNavigationBar (wrapping the icon)
BottomNavigationBar(
  items: [
    BottomNavigationBarItem(
      icon: Badge(
        label: Text('$_count'),
        isLabelVisible: _count > 0,
        child: Icon(Icons.mail_outline),
      ),
      activeIcon: Badge(
        label: Text('$_count'),
        isLabelVisible: _count > 0,
        child: Icon(Icons.mail),
      ),
      label: 'Inbox',
    ),
  ],
)
```

---

## NavigationRail

Vertical navigation — good for tablet/desktop layouts.

```dart
Row(
  children: [
    NavigationRail(
      selectedIndex: _selectedIndex,
      onDestinationSelected: (index) => setState(() => _selectedIndex = index),
      extended: _isExtended,   // true = shows labels next to icons
      minWidth: 56,
      minExtendedWidth: 180,
      backgroundColor: Colors.grey[100],
      elevation: 4,
      indicatorColor: Colors.blue[100],
      selectedIconTheme: IconThemeData(color: Colors.blue),
      unselectedIconTheme: IconThemeData(color: Colors.grey),
      selectedLabelTextStyle: TextStyle(color: Colors.blue, fontWeight: FontWeight.w600),
      unselectedLabelTextStyle: TextStyle(color: Colors.grey),
      labelType: NavigationRailLabelType.all,   // none, selected, all
      leading: FloatingActionButton(
        elevation: 0,
        onPressed: () {},
        child: Icon(Icons.add),
      ),
      trailing: IconButton(
        icon: Icon(_isExtended ? Icons.chevron_left : Icons.chevron_right),
        onPressed: () => setState(() => _isExtended = !_isExtended),
      ),
      groupAlignment: 0.0,   // -1.0 = top, 0.0 = center, 1.0 = bottom
      destinations: [
        NavigationRailDestination(
          icon: Icon(Icons.home_outlined),
          selectedIcon: Icon(Icons.home),
          label: Text('Home'),
        ),
        NavigationRailDestination(
          icon: Icon(Icons.search),
          label: Text('Search'),
        ),
        NavigationRailDestination(
          icon: Badge(label: Text('5'), child: Icon(Icons.notifications_outlined)),
          selectedIcon: Badge(label: Text('5'), child: Icon(Icons.notifications)),
          label: Text('Notifications'),
        ),
      ],
    ),
    VerticalDivider(thickness: 1, width: 1),
    Expanded(child: _screens[_selectedIndex]),
  ],
)
```

---

## BottomAppBar

Used with a FAB for a notched or rounded bottom bar.

```dart
Scaffold(
  floatingActionButton: FloatingActionButton(
    onPressed: () {},
    child: Icon(Icons.add),
  ),
  floatingActionButtonLocation: FloatingActionButtonLocation.centerDocked,
  bottomNavigationBar: BottomAppBar(
    shape: CircularNotchedRectangle(),   // notch for FAB
    notchMargin: 8,
    color: Colors.white,
    elevation: 8,
    height: 60,
    padding: EdgeInsets.zero,
    child: Row(
      mainAxisAlignment: MainAxisAlignment.spaceAround,
      children: [
        IconButton(icon: Icon(Icons.home), onPressed: () {}),
        IconButton(icon: Icon(Icons.search), onPressed: () {}),
        SizedBox(width: 48),   // space for FAB
        IconButton(icon: Icon(Icons.favorite), onPressed: () {}),
        IconButton(icon: Icon(Icons.person), onPressed: () {}),
      ],
    ),
  ),
)
```

---

## Material 3 Components

### NavigationBar (M3 replacement for BottomNavigationBar)
```dart
NavigationBar(
  selectedIndex: _selectedIndex,
  onDestinationSelected: (i) => setState(() => _selectedIndex = i),
  backgroundColor: Colors.white,
  indicatorColor: Colors.blue[100],
  elevation: 3,
  height: 80,
  animationDuration: Duration(milliseconds: 500),
  labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,  // alwaysHide, onlyShowSelected
  destinations: [
    NavigationDestination(
      icon: Icon(Icons.home_outlined),
      selectedIcon: Icon(Icons.home),
      label: 'Home',
      tooltip: 'Go to home',
    ),
    NavigationDestination(
      icon: Badge(child: Icon(Icons.notifications_outlined)),
      selectedIcon: Badge(label: Text('3'), child: Icon(Icons.notifications)),
      label: 'Alerts',
    ),
    NavigationDestination(
      icon: Icon(Icons.person_outline),
      selectedIcon: Icon(Icons.person),
      label: 'Profile',
    ),
  ],
)
```

### NavigationDrawer (M3)
```dart
NavigationDrawer(
  selectedIndex: _selectedIndex,
  onDestinationSelected: (index) {
    setState(() => _selectedIndex = index);
    Navigator.pop(context);
  },
  children: [
    Padding(
      padding: EdgeInsets.fromLTRB(28, 16, 16, 10),
      child: Text('Mail', style: Theme.of(context).textTheme.titleSmall),
    ),
    NavigationDrawerDestination(
      icon: Icon(Icons.inbox_outlined),
      selectedIcon: Icon(Icons.inbox),
      label: Text('Inbox'),
      badge: Badge(label: Text('24')),
    ),
    NavigationDrawerDestination(
      icon: Icon(Icons.send_outlined),
      selectedIcon: Icon(Icons.send),
      label: Text('Sent'),
    ),
    Divider(indent: 28, endIndent: 28),
    Padding(
      padding: EdgeInsets.fromLTRB(28, 16, 16, 10),
      child: Text('Labels', style: Theme.of(context).textTheme.titleSmall),
    ),
    NavigationDrawerDestination(
      icon: Icon(Icons.star_outline),
      selectedIcon: Icon(Icons.star),
      label: Text('Starred'),
    ),
  ],
)
```

### SegmentedButton (M3 replacement for ToggleButtons)
```dart
SegmentedButton<String>(
  selected: _selectedSegments,
  onSelectionChanged: (Set<String> selection) {
    setState(() => _selectedSegments = selection);
  },
  multiSelectionEnabled: false,   // single or multi selection
  emptySelectionAllowed: false,
  style: ButtonStyle(
    backgroundColor: MaterialStateProperty.resolveWith<Color>((states) {
      if (states.contains(MaterialState.selected)) return Colors.blue;
      return Colors.transparent;
    }),
  ),
  segments: [
    ButtonSegment<String>(
      value: 'day',
      label: Text('Day'),
      icon: Icon(Icons.view_day),
    ),
    ButtonSegment<String>(
      value: 'week',
      label: Text('Week'),
      icon: Icon(Icons.view_week),
    ),
    ButtonSegment<String>(
      value: 'month',
      label: Text('Month'),
      icon: Icon(Icons.calendar_view_month),
    ),
  ],
)
```

### SearchBar (M3)
```dart
SearchBar(
  controller: _searchController,
  hintText: 'Search...',
  leading: Icon(Icons.search),
  trailing: [
    _searchController.text.isNotEmpty
        ? IconButton(
            icon: Icon(Icons.clear),
            onPressed: () => _searchController.clear(),
          )
        : Icon(Icons.mic),
  ],
  onChanged: (value) => _performSearch(value),
  onSubmitted: (value) => _performSearch(value),
  padding: MaterialStateProperty.all(EdgeInsets.symmetric(horizontal: 16)),
  elevation: MaterialStateProperty.all(3),
  backgroundColor: MaterialStateProperty.all(Colors.white),
  shadowColor: MaterialStateProperty.all(Colors.black26),
  shape: MaterialStateProperty.all(
    RoundedRectangleBorder(borderRadius: BorderRadius.circular(28)),
  ),
)
```

### SearchAnchor (M3 — search with overlay)
```dart
SearchAnchor(
  builder: (context, controller) {
    return SearchBar(
      controller: controller,
      onTap: () => controller.openView(),
      onChanged: (_) => controller.openView(),
      leading: Icon(Icons.search),
      hintText: 'Search...',
    );
  },
  suggestionsBuilder: (context, controller) {
    return _suggestions
        .where((s) => s.toLowerCase().contains(controller.text.toLowerCase()))
        .map((s) => ListTile(
              title: Text(s),
              onTap: () {
                setState(() => _query = s);
                controller.closeView(s);
              },
            ))
        .toList();
  },
)
```

### FilledButton (M3)
```dart
FilledButton(
  onPressed: () {},
  style: FilledButton.styleFrom(
    backgroundColor: Colors.blue,
    foregroundColor: Colors.white,
    minimumSize: Size(120, 44),
    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
  ),
  child: Text('Continue'),
)

FilledButton.tonal(   // softer filled variant
  onPressed: () {},
  child: Text('Secondary Action'),
)

FilledButton.icon(
  onPressed: () {},
  icon: Icon(Icons.check),
  label: Text('Confirm'),
)
```

### Card variants (M3)
```dart
// Elevated card (default)
Card(elevation: 2, child: ...)

// Filled card
Card.filled(child: ...)

// Outlined card
Card.outlined(child: ...)
```

---

## Hero Animation

Shared element transition between routes.

```dart
// Source screen
Hero(
  tag: 'product-image-${product.id}',   // must be unique across the screen
  child: ClipRRect(
    borderRadius: BorderRadius.circular(8),
    child: Image.network(product.imageUrl, width: 100, height: 100, fit: BoxFit.cover),
  ),
)

// Destination screen (same tag)
Hero(
  tag: 'product-image-${product.id}',
  child: Image.network(product.imageUrl, width: double.infinity, fit: BoxFit.cover),
)

// Custom flight animation
Hero(
  tag: 'avatar',
  flightShuttleBuilder: (context, animation, direction, fromContext, toContext) {
    return AnimatedBuilder(
      animation: animation,
      builder: (context, child) => Opacity(opacity: animation.value, child: child),
      child: toContext.widget,
    );
  },
  createRectTween: (begin, end) => RectTween(begin: begin, end: end),
  child: CircleAvatar(backgroundImage: NetworkImage(avatarUrl)),
)
```

---

## AnimationController & Tween

### Basic setup
```dart
class _AnimatedWidgetState extends State<AnimatedWidget>
    with SingleTickerProviderStateMixin {     // TickerProviderStateMixin for multiple

  late AnimationController _controller;
  late Animation<double> _fadeAnimation;
  late Animation<Offset> _slideAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: Duration(milliseconds: 600),
      reverseDuration: Duration(milliseconds: 400),
      lowerBound: 0.0,
      upperBound: 1.0,
    );

    _fadeAnimation = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeIn),
    );

    _slideAnimation = Tween<Offset>(
      begin: Offset(0, 0.5),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _controller, curve: Curves.easeOut));

    _controller.forward();  // start animation
  }

  @override
  void dispose() {
    _controller.dispose();   // IMPORTANT: always dispose
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SlideTransition(
      position: _slideAnimation,
      child: FadeTransition(
        opacity: _fadeAnimation,
        child: YourWidget(),
      ),
    );
  }
}
```

### AnimationController methods
```dart
_controller.forward()           // 0.0 → 1.0
_controller.reverse()           // 1.0 → 0.0
_controller.repeat()            // loop forever
_controller.repeat(reverse: true)  // ping-pong
_controller.stop()
_controller.reset()             // back to 0.0
_controller.animateTo(0.5, duration: Duration(ms: 200), curve: Curves.ease)
_controller.value               // current value
_controller.status              // AnimationStatus: forward, reverse, completed, dismissed
_controller.addListener(() {})  // called every tick
_controller.addStatusListener((status) {})
```

### Common Curves
```dart
Curves.linear
Curves.easeIn       Curves.easeOut      Curves.easeInOut
Curves.easeInBack   Curves.easeOutBack  Curves.easeInOutBack
Curves.bounceIn     Curves.bounceOut    Curves.bounceInOut
Curves.elasticIn    Curves.elasticOut   Curves.elasticInOut
Curves.decelerate
Curves.fastOutSlowIn
Curves.slowMiddle

// Custom cubic bezier
Cubic(0.4, 0.0, 0.2, 1.0)
```

### Common Tweens
```dart
Tween<double>(begin: 0, end: 1)
Tween<Offset>(begin: Offset.zero, end: Offset(1, 0))
ColorTween(begin: Colors.red, end: Colors.blue)
SizeTween(begin: Size(100, 100), end: Size(200, 200))
RectTween(begin: Rect.fromLTWH(0,0,100,100), end: Rect.fromLTWH(100,100,200,200))
IntTween(begin: 0, end: 100)
StepTween(begin: 0, end: 5)

// Sequence (chain animations)
TweenSequence<double>([
  TweenSequenceItem(tween: Tween(begin: 0, end: 1), weight: 40),
  TweenSequenceItem(tween: ConstantTween(1), weight: 20),
  TweenSequenceItem(tween: Tween(begin: 1, end: 0), weight: 40),
])

// Interval (only animate during a portion of the controller)
CurvedAnimation(
  parent: _controller,
  curve: Interval(0.0, 0.5, curve: Curves.easeIn),  // animate from 0% to 50%
)
```

---

## TweenAnimationBuilder

Animates to a new `end` value whenever it changes — no controller needed.

```dart
TweenAnimationBuilder<double>(
  tween: Tween<double>(begin: 0, end: _targetValue),
  duration: Duration(milliseconds: 500),
  curve: Curves.easeInOut,
  onEnd: () => print('Animation complete'),
  builder: (context, value, child) {
    return Transform.scale(
      scale: value,
      child: child,
    );
  },
  child: Icon(Icons.star, size: 48, color: Colors.amber),  // static child
)

// Color animation
TweenAnimationBuilder<Color?>(
  tween: ColorTween(begin: Colors.blue, end: _isDark ? Colors.grey[900] : Colors.white),
  duration: Duration(milliseconds: 300),
  builder: (context, color, child) => Container(
    color: color,
    child: child,
  ),
  child: MyContent(),
)
```

---

## AnimatedBuilder

For animating complex widgets using an existing AnimationController.

```dart
AnimatedBuilder(
  animation: _controller,   // any Listenable works (controller, animation, notifier)
  builder: (context, child) {
    return Transform(
      transform: Matrix4.rotationZ(_controller.value * 2 * pi),
      alignment: Alignment.center,
      child: child,
    );
  },
  child: Icon(Icons.refresh, size: 48),  // not rebuilt on animation tick
)

// Multiple animations
AnimatedBuilder(
  animation: Listenable.merge([_controller1, _controller2]),
  builder: (context, child) {
    return Opacity(
      opacity: _fadeAnimation.value,
      child: Transform.translate(
        offset: Offset(_slideAnimation.value, 0),
        child: child,
      ),
    );
  },
  child: MyWidget(),
)
```

---

## AnimatedList

List that animates item insertions and removals.

```dart
class _AnimatedListState extends State<AnimatedListDemo> {
  final _listKey = GlobalKey<AnimatedListState>();
  final _items = <String>[];

  void _addItem() {
    final index = _items.length;
    _items.add('Item ${index + 1}');
    _listKey.currentState!.insertItem(
      index,
      duration: Duration(milliseconds: 400),
    );
  }

  void _removeItem(int index) {
    final item = _items[index];
    _listKey.currentState!.removeItem(
      index,
      (context, animation) => _buildAnimatedItem(item, animation),
      duration: Duration(milliseconds: 300),
    );
    _items.removeAt(index);
  }

  Widget _buildAnimatedItem(String item, Animation<double> animation) {
    return SizeTransition(
      sizeFactor: animation,
      child: FadeTransition(
        opacity: animation,
        child: ListTile(
          title: Text(item),
          trailing: IconButton(
            icon: Icon(Icons.delete),
            onPressed: () => _removeItem(_items.indexOf(item)),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedList(
      key: _listKey,
      initialItemCount: _items.length,
      itemBuilder: (context, index, animation) {
        return _buildAnimatedItem(_items[index], animation);
      },
    );
  }
}
```

---

## Transition Widgets

Pre-built animated widgets that take an `Animation<T>`.

```dart
// Fade
FadeTransition(
  opacity: _controller,  // Animation<double> 0.0 to 1.0
  child: MyWidget(),
)

// Slide
SlideTransition(
  position: Tween<Offset>(begin: Offset(1, 0), end: Offset.zero)
      .animate(CurvedAnimation(parent: _controller, curve: Curves.easeOut)),
  child: MyWidget(),
)

// Scale
ScaleTransition(
  scale: CurvedAnimation(parent: _controller, curve: Curves.elasticOut),
  alignment: Alignment.center,
  child: MyWidget(),
)

// Rotation
RotationTransition(
  turns: _controller,   // 1.0 = full 360°
  child: Icon(Icons.refresh),
)

// Size (clip animation)
SizeTransition(
  sizeFactor: _controller,
  axis: Axis.vertical,
  axisAlignment: -1,   // -1 = expand from top, 1 = expand from bottom
  child: Container(height: 200, color: Colors.blue),
)

// Align transition
AlignTransition(
  alignment: Tween<AlignmentGeometry>(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  ).animate(_controller),
  child: Icon(Icons.circle),
)

// Default text style transition
DefaultTextStyleTransition(
  style: TextStyleTween(
    begin: TextStyle(color: Colors.blue, fontSize: 14),
    end: TextStyle(color: Colors.red, fontSize: 24),
  ).animate(_controller),
  child: Text('Animated Text'),
)

// Decorated box transition
DecoratedBoxTransition(
  decoration: DecorationTween(
    begin: BoxDecoration(color: Colors.blue, borderRadius: BorderRadius.circular(0)),
    end: BoxDecoration(color: Colors.purple, borderRadius: BorderRadius.circular(24)),
  ).animate(_controller),
  child: SizedBox(width: 100, height: 100),
)
```

---

## CustomPaint & Canvas

For drawing custom graphics.

```dart
CustomPaint(
  size: Size(300, 300),    // if no child, must specify size
  painter: MyPainter(),    // drawn behind child
  foregroundPainter: MyOverlayPainter(),  // drawn in front of child
  child: Container(/* optional */),
  willChange: true,   // hint for optimization during animation
)

// The painter class
class MyPainter extends CustomPainter {
  final double progress;  // pass in animation value
  MyPainter(this.progress);

  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.blue
      ..strokeWidth = 4
      ..style = PaintingStyle.stroke    // stroke or fill
      ..strokeCap = StrokeCap.round
      ..strokeJoin = StrokeJoin.round
      ..isAntiAlias = true;

    // Draw shapes
    canvas.drawCircle(Offset(size.width / 2, size.height / 2), 80, paint);
    canvas.drawLine(Offset(0, 0), Offset(size.width, size.height), paint);
    canvas.drawRect(Rect.fromLTWH(10, 10, 100, 80), paint..style = PaintingStyle.fill);
    canvas.drawRRect(
      RRect.fromRectAndRadius(Rect.fromLTWH(10, 10, 100, 80), Radius.circular(12)),
      paint,
    );

    // Arc (progress circle)
    canvas.drawArc(
      Rect.fromCircle(center: Offset(size.width / 2, size.height / 2), radius: 80),
      -pi / 2,           // start angle (top)
      2 * pi * progress, // sweep angle
      false,             // useCenter: true draws pie slices
      paint,
    );

    // Path (arbitrary shapes)
    final path = Path()
      ..moveTo(size.width / 2, 0)
      ..lineTo(size.width, size.height)
      ..lineTo(0, size.height)
      ..close();
    canvas.drawPath(path, paint);

    // Draw text
    final textPainter = TextPainter(
      text: TextSpan(text: '${(progress * 100).toInt()}%',
          style: TextStyle(color: Colors.blue, fontSize: 24, fontWeight: FontWeight.bold)),
      textDirection: TextDirection.ltr,
    )..layout();
    textPainter.paint(
      canvas,
      Offset(size.width / 2 - textPainter.width / 2,
             size.height / 2 - textPainter.height / 2),
    );

    // Save/restore layer
    canvas.save();
    canvas.translate(50, 50);
    canvas.rotate(pi / 4);
    canvas.drawRect(Rect.fromLTWH(-20, -20, 40, 40), paint);
    canvas.restore();

    // Gradient paint
    final gradientPaint = Paint()
      ..shader = LinearGradient(
        colors: [Colors.blue, Colors.purple],
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
      ).createShader(Rect.fromLTWH(0, 0, size.width, size.height));
    canvas.drawRect(Rect.fromLTWH(0, 0, size.width, size.height), gradientPaint);
  }

  @override
  bool shouldRepaint(MyPainter oldDelegate) => oldDelegate.progress != progress;
}
```

---

## Transform

Apply matrix transformations to a widget.

```dart
// Rotate
Transform.rotate(
  angle: pi / 4,              // radians (pi = 180°)
  alignment: Alignment.center,
  child: Container(width: 100, height: 100, color: Colors.blue),
)

// Scale
Transform.scale(
  scale: 1.5,
  scaleX: 1.2,  // individual axes (Flutter 3.x)
  scaleY: 0.8,
  alignment: Alignment.center,
  child: MyWidget(),
)

// Translate (move without affecting layout)
Transform.translate(
  offset: Offset(20, -10),
  child: MyWidget(),
)

// Flip horizontally
Transform.flip(
  flipX: true,
  child: Icon(Icons.arrow_forward),
)

// Full matrix (3D perspective)
Transform(
  transform: Matrix4.identity()
    ..setEntry(3, 2, 0.001)   // perspective
    ..rotateX(0.3)
    ..rotateY(0.3),
  alignment: Alignment.center,
  child: Container(width: 200, height: 200, color: Colors.blue),
)
```

---

## BackdropFilter & ImageFilter

Apply blur/color matrix to whatever is behind the widget.

```dart
// Blur (frosted glass effect)
Stack(
  children: [
    BackgroundImage(),
    BackdropFilter(
      filter: ImageFilter.blur(sigmaX: 10, sigmaY: 10),
      child: Container(
        color: Colors.white.withOpacity(0.2),  // tint on top of blur
        child: Text('Frosted Glass'),
      ),
    ),
  ],
)

// ClipRRect + BackdropFilter for rounded frosted glass card
ClipRRect(
  borderRadius: BorderRadius.circular(16),
  child: BackdropFilter(
    filter: ImageFilter.blur(sigmaX: 16, sigmaY: 16),
    child: Container(
      padding: EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.15),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.3)),
      ),
      child: child,
    ),
  ),
)

// Dilate / Erode
ImageFilter.dilate(radiusX: 3, radiusY: 3)
ImageFilter.erode(radiusX: 2, radiusY: 2)

// Matrix (color manipulation)
ImageFilter.matrix(Matrix4.rotationZ(0.1).storage)
```

---

## ShaderMask

Applies a gradient or shader as a mask.

```dart
// Fade-out text at the bottom
ShaderMask(
  shaderCallback: (bounds) => LinearGradient(
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
    colors: [Colors.black, Colors.transparent],
    stops: [0.5, 1.0],
  ).createShader(bounds),
  blendMode: BlendMode.dstIn,
  child: Text(longText, maxLines: 5, overflow: TextOverflow.fade),
)

// Rainbow text
ShaderMask(
  shaderCallback: (bounds) => LinearGradient(
    colors: [Colors.red, Colors.orange, Colors.yellow, Colors.green, Colors.blue, Colors.purple],
  ).createShader(Rect.fromLTWH(0, 0, bounds.width, bounds.height)),
  blendMode: BlendMode.srcIn,
  child: Text('Rainbow!', style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold)),
)
```

---

## ColorFiltered

Apply color filters to child widgets.

```dart
// Grayscale image
ColorFiltered(
  colorFilter: ColorFilter.matrix([
    0.2126, 0.7152, 0.0722, 0, 0,
    0.2126, 0.7152, 0.0722, 0, 0,
    0.2126, 0.7152, 0.0722, 0, 0,
    0, 0, 0, 1, 0,
  ]),
  child: Image.asset('photo.png'),
)

// Sepia tone
ColorFiltered(
  colorFilter: ColorFilter.matrix([
    0.393, 0.769, 0.189, 0, 0,
    0.349, 0.686, 0.168, 0, 0,
    0.272, 0.534, 0.131, 0, 0,
    0, 0, 0, 1, 0,
  ]),
  child: Image.asset('photo.png'),
)

// Tint
ColorFiltered(
  colorFilter: ColorFilter.mode(Colors.blue.withOpacity(0.4), BlendMode.srcATop),
  child: Image.asset('photo.png'),
)
```

---

## AspectRatio

Forces a widget to maintain a specific width-to-height ratio.

```dart
AspectRatio(
  aspectRatio: 16 / 9,   // width / height
  child: VideoPlayer(),
)

// Square thumbnail
AspectRatio(
  aspectRatio: 1,
  child: Image.network(url, fit: BoxFit.cover),
)
```

---

## FittedBox

Scales and positions its child within available space.

```dart
FittedBox(
  fit: BoxFit.contain,      // same values as Image fit
  alignment: Alignment.center,
  child: Text(
    '99+',
    style: TextStyle(fontSize: 100),  // large font, FittedBox scales it down
  ),
)

// Icon that fills its container
SizedBox(
  width: 60,
  height: 60,
  child: FittedBox(
    fit: BoxFit.fill,
    child: Icon(Icons.star),
  ),
)
```

---

## FractionallySizedBox

Sizes child as a fraction of parent size.

```dart
// 80% width, centered
Align(
  alignment: Alignment.center,
  child: FractionallySizedBox(
    widthFactor: 0.8,
    child: ElevatedButton(onPressed: () {}, child: Text('Wide Button')),
  ),
)

// In Column, 50% height
FractionallySizedBox(
  heightFactor: 0.5,
  child: Container(color: Colors.blue),
)

// SliverFractionallySizedBox in sliver context
SliverFractionalPadding(paddingFraction: 0.1)
```

---

## IntrinsicWidth & IntrinsicHeight

Sizes a widget to the intrinsic (natural) size of its largest child.
> ⚠️ Expensive — avoid in large lists.

```dart
// Makes all buttons the same width (the width of the widest one)
IntrinsicWidth(
  child: Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,  // stretch to intrinsic width
    children: [
      ElevatedButton(onPressed: () {}, child: Text('Short')),
      ElevatedButton(onPressed: () {}, child: Text('A Much Longer Button')),
      ElevatedButton(onPressed: () {}, child: Text('OK')),
    ],
  ),
)

// Row with items of equal height
IntrinsicHeight(
  child: Row(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      ColoredBox(color: Colors.red, child: Text('Short')),
      VerticalDivider(),
      ColoredBox(color: Colors.blue, child: Text('Tall\nMultiline\nContent')),
    ],
  ),
)
```

---

## LimitedBox

Limits size only when unconstrained (unbounded constraints).

```dart
// In a ListView, give a default max height
ListView(
  children: [
    LimitedBox(
      maxHeight: 200,
      child: Container(color: Colors.blue),  // won't exceed 200px tall
    ),
  ],
)
```

---

## OverflowBox

Allows a child to be larger than the parent (clips by default).

```dart
SizedBox(
  width: 100,
  height: 100,
  child: OverflowBox(
    maxWidth: 200,     // allow child to be up to 200px wide
    maxHeight: 200,
    alignment: Alignment.center,
    child: Container(width: 180, height: 180, color: Colors.blue),
  ),
)
```

---

## CustomLayout

### CustomSingleChildLayout
```dart
class _BottomCenterDelegate extends SingleChildLayoutDelegate {
  final double offset;
  _BottomCenterDelegate(this.offset);

  @override
  Offset getPositionForChild(Size size, Size childSize) {
    return Offset(
      (size.width - childSize.width) / 2,
      size.height - childSize.height - offset,
    );
  }

  @override
  bool shouldRelayout(_BottomCenterDelegate old) => old.offset != offset;
}

CustomSingleChildLayout(
  delegate: _BottomCenterDelegate(20),
  child: Tooltip(message: 'Positioned by delegate'),
)
```

### CustomMultiChildLayout
```dart
class _DashboardDelegate extends MultiChildLayoutDelegate {
  @override
  void performLayout(Size size) {
    final headerSize = layoutChild('header', BoxConstraints.loose(size));
    positionChild('header', Offset.zero);

    final bodyHeight = size.height - headerSize.height;
    layoutChild('body', BoxConstraints(
      maxWidth: size.width,
      maxHeight: bodyHeight,
    ));
    positionChild('body', Offset(0, headerSize.height));
  }

  @override
  bool shouldRelayout(_DashboardDelegate old) => false;
}

CustomMultiChildLayout(
  delegate: _DashboardDelegate(),
  children: [
    LayoutId(id: 'header', child: AppHeader()),
    LayoutId(id: 'body', child: AppBody()),
  ],
)
```

---

## Flow

Efficient widget for custom layouts (like fan menus, docks).

```dart
Flow(
  delegate: _FanMenuDelegate(animation: _controller),
  children: icons.map((icon) => FloatingActionButton(
    mini: true,
    onPressed: () {},
    child: Icon(icon),
  )).toList(),
)

class _FanMenuDelegate extends FlowDelegate {
  final Animation<double> animation;
  _FanMenuDelegate({required this.animation}) : super(repaint: animation);

  @override
  void paintChildren(FlowPaintingContext context) {
    for (int i = context.childCount - 1; i >= 0; i--) {
      final dx = -i * 60.0 * animation.value;
      context.paintChild(i, transform: Matrix4.translationValues(dx, 0, 0));
    }
  }

  @override
  bool shouldRepaint(_FanMenuDelegate old) => animation != old.animation;
}
```

---

## Baseline

Aligns child by text baseline.

```dart
Row(
  crossAxisAlignment: CrossAxisAlignment.baseline,
  textBaseline: TextBaseline.alphabetic,
  children: [
    Text('$24.99', style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold)),
    Text(' / month', style: TextStyle(fontSize: 14, color: Colors.grey)),
  ],
)
```

---

## AbsorbPointer & IgnorePointer

### AbsorbPointer — blocks all touches (widget still visible)
```dart
AbsorbPointer(
  absorbing: _isLoading,   // true = disable interactions
  child: ElevatedButton(
    onPressed: _submit,
    child: Text('Submit'),
  ),
)
```

### IgnorePointer — passes through to widgets behind
```dart
IgnorePointer(
  ignoring: true,
  child: Overlay(
    // overlay that shouldn't capture touches
  ),
)
```

---

## MouseRegion

Detects mouse cursor entry/exit/movement (desktop/web).

```dart
MouseRegion(
  onEnter: (event) => setState(() => _isHovered = true),
  onExit: (event) => setState(() => _isHovered = false),
  onHover: (event) => setState(() => _mousePosition = event.localPosition),
  cursor: SystemMouseCursors.click,  // custom cursor on hover
  child: AnimatedContainer(
    duration: Duration(milliseconds: 200),
    color: _isHovered ? Colors.blue[100] : Colors.transparent,
    child: Text('Hover me'),
  ),
)
```

### SystemMouseCursors
```dart
SystemMouseCursors.basic       // default arrow
SystemMouseCursors.click       // pointer hand
SystemMouseCursors.forbidden   // no sign
SystemMouseCursors.grab        // grab/open hand
SystemMouseCursors.grabbing    // closed hand
SystemMouseCursors.text        // I-beam
SystemMouseCursors.resizeLeft
SystemMouseCursors.resizeRight
SystemMouseCursors.wait        // loading/busy
```

---

## Draggable & DragTarget

Drag-and-drop between widgets.

```dart
// Draggable source
Draggable<String>(
  data: 'my_data',
  feedback: Material(
    elevation: 4,
    child: Container(
      padding: EdgeInsets.all(8),
      color: Colors.blue,
      child: Text('Dragging!', style: TextStyle(color: Colors.white)),
    ),
  ),
  childWhenDragging: Opacity(opacity: 0.3, child: OriginalWidget()),
  dragAnchorStrategy: pointerDragAnchorStrategy,  // cursor at pointer
  axis: null,    // null = both axes; Axis.horizontal / .vertical to constrain
  onDragStarted: () => print('Started'),
  onDragEnd: (details) => print('Ended at ${details.offset}'),
  onDraggableCanceled: (velocity, offset) => print('Cancelled'),
  child: OriginalWidget(),
)

// Drop target
DragTarget<String>(
  onWillAcceptWithDetails: (details) {
    return details.data.startsWith('my_');   // return true to allow drop
  },
  onAcceptWithDetails: (details) {
    setState(() => _droppedData = details.data);
  },
  onLeave: (data) => print('Left target'),
  builder: (context, candidateData, rejectedData) {
    final isHovering = candidateData.isNotEmpty;
    return AnimatedContainer(
      duration: Duration(milliseconds: 200),
      width: 150,
      height: 150,
      decoration: BoxDecoration(
        color: isHovering ? Colors.blue[100] : Colors.grey[100],
        border: Border.all(
          color: isHovering ? Colors.blue : Colors.grey,
          width: isHovering ? 2 : 1,
        ),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Center(child: Text(_droppedData ?? 'Drop here')),
    );
  },
)

// Long press draggable
LongPressDraggable<int>(
  data: itemIndex,
  delay: Duration(milliseconds: 300),
  feedback: DragFeedback(),
  child: ListItem(),
)
```

---

## InteractiveViewer

Pan and zoom a widget.

```dart
InteractiveViewer(
  minScale: 0.5,
  maxScale: 4.0,
  boundaryMargin: EdgeInsets.all(20),
  panEnabled: true,
  scaleEnabled: true,
  constrained: true,   // false = content can be larger than widget
  onInteractionStart: (details) {},
  onInteractionUpdate: (details) {
    print('Scale: ${details.scale}');
    print('Focal point: ${details.focalPoint}');
  },
  onInteractionEnd: (details) {},
  transformationController: TransformationController(),
  clipBehavior: Clip.hardEdge,
  child: Image.asset('map.png'),
)

// Programmatic control with TransformationController
final _transformController = TransformationController();

void _zoomReset() {
  _transformController.value = Matrix4.identity();
}

void _zoomToPoint(Offset point) {
  final scale = 2.0;
  final x = -point.dx * (scale - 1);
  final y = -point.dy * (scale - 1);
  _transformController.value = Matrix4.identity()
    ..translate(x, y)
    ..scale(scale);
}
```

---

## SelectableText

Like `Text` but allows user to select/copy content.

```dart
SelectableText(
  'This text can be selected and copied.',
  style: TextStyle(fontSize: 16),
  textAlign: TextAlign.left,
  maxLines: null,
  cursorColor: Colors.blue,
  cursorWidth: 2,
  showCursor: false,
  autofocus: false,
  enableInteractiveSelection: true,
  selectionControls: MaterialTextSelectionControls(),
  onTap: () => print('Tapped'),
  onSelectionChanged: (selection, cause) {
    final selected = 'full text'.substring(selection.start, selection.end);
    print('Selected: $selected');
  },
  contextMenuBuilder: (context, editableTextState) {
    return AdaptiveTextSelectionToolbar.editableText(
      editableTextState: editableTextState,
    );
  },
)

// Rich selectable text
SelectableText.rich(
  TextSpan(children: [
    TextSpan(text: 'Bold ', style: TextStyle(fontWeight: FontWeight.bold)),
    TextSpan(text: 'and italic', style: TextStyle(fontStyle: FontStyle.italic)),
  ]),
)
```

---

## Focus & FocusScope

Manual focus management.

```dart
// FocusNode usage
class _FormState extends State<MyForm> {
  final _nameFocus = FocusNode();
  final _emailFocus = FocusNode();

  @override
  void initState() {
    super.initState();
    _nameFocus.addListener(() {
      if (!_nameFocus.hasFocus) _validateName();
    });
  }

  @override
  void dispose() {
    _nameFocus.dispose();
    _emailFocus.dispose();
    super.dispose();
  }

  // Move focus
  void _nextField() => FocusScope.of(context).requestFocus(_emailFocus);
  void _unfocus() => FocusScope.of(context).unfocus();
  void _focusFirst() => FocusScope.of(context).requestFocus(_nameFocus);

  @override
  Widget build(BuildContext context) {
    return Column(children: [
      TextField(focusNode: _nameFocus, onSubmitted: (_) => _nextField()),
      TextField(focusNode: _emailFocus, onSubmitted: (_) => _unfocus()),
    ]);
  }
}

// Focus widget (for keyboard shortcuts, desktop)
Focus(
  focusNode: _focusNode,
  autofocus: true,
  onKeyEvent: (node, event) {
    if (event is KeyDownEvent && event.logicalKey == LogicalKeyboardKey.escape) {
      _close();
      return KeyEventResult.handled;
    }
    return KeyEventResult.ignored;
  },
  child: MyWidget(),
)
```

---

## Actions & Shortcuts

Keyboard shortcut handling for desktop/web apps.

```dart
// Define intents
class SaveIntent extends Intent {
  const SaveIntent();
}

class UndoIntent extends Intent {
  const UndoIntent();
}

// Wrap with Shortcuts + Actions
Shortcuts(
  shortcuts: {
    SingleActivator(LogicalKeyboardKey.keyS, control: true): SaveIntent(),
    SingleActivator(LogicalKeyboardKey.keyZ, control: true): UndoIntent(),
    SingleActivator(LogicalKeyboardKey.keyZ, control: true, shift: true): RedoIntent(),
  },
  child: Actions(
    actions: {
      SaveIntent: CallbackAction<SaveIntent>(onInvoke: (_) => _save()),
      UndoIntent: CallbackAction<UndoIntent>(onInvoke: (_) => _undo()),
    },
    child: Focus(
      autofocus: true,
      child: MyEditor(),
    ),
  ),
)
```

---

## WillPopScope / PopScope

Intercept back navigation.

```dart
// Flutter 3.12+ use PopScope
PopScope(
  canPop: false,   // false = prevent automatic pop
  onPopInvoked: (bool didPop) async {
    if (didPop) return;
    final shouldPop = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Discard changes?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: Text('No')),
          TextButton(onPressed: () => Navigator.pop(context, true), child: Text('Yes')),
        ],
      ),
    );
    if (shouldPop == true && context.mounted) {
      Navigator.pop(context);
    }
  },
  child: MyScreen(),
)

// Legacy (Flutter < 3.12)
WillPopScope(
  onWillPop: () async {
    return await showConfirmDialog(context) ?? false;
  },
  child: MyScreen(),
)
```

---

## NotificationListener

Listens for notifications that bubble up the widget tree.

```dart
// Scroll notifications
NotificationListener<ScrollNotification>(
  onNotification: (notification) {
    if (notification is ScrollStartNotification) {
      print('Scroll started');
    } else if (notification is ScrollUpdateNotification) {
      final pixels = notification.metrics.pixels;
      final maxScroll = notification.metrics.maxScrollExtent;
      final progress = pixels / maxScroll;
      setState(() => _scrollProgress = progress);
    } else if (notification is ScrollEndNotification) {
      print('Scroll ended');
    } else if (notification is OverscrollNotification) {
      print('Overscrolled by ${notification.overscroll}');
    }
    return false;   // false = allow bubble to continue up; true = stop
  },
  child: ListView.builder(itemCount: 100, itemBuilder: (_, i) => ListTile(title: Text('$i'))),
)

// Custom notification
class MyNotification extends Notification {
  final String message;
  MyNotification(this.message);
}

// Dispatch from child
MyNotification('hello').dispatch(context);

// Listen in ancestor
NotificationListener<MyNotification>(
  onNotification: (n) { print(n.message); return true; },
  child: child,
)
```

---

## Scrollbar

Displays a scrollbar over a scrollable widget.

```dart
Scrollbar(
  controller: _scrollController,
  thumbVisibility: true,     // always show thumb
  trackVisibility: true,     // show track
  interactive: true,         // allow thumb dragging
  thickness: 8,
  radius: Radius.circular(4),
  scrollbarOrientation: ScrollbarOrientation.right,
  child: ListView.builder(
    controller: _scrollController,
    itemCount: 100,
    itemBuilder: (_, i) => ListTile(title: Text('Item $i')),
  ),
)

// RawScrollbar for full custom control
RawScrollbar(
  controller: _controller,
  thumbColor: Colors.blue,
  trackColor: Colors.grey[200],
  thumbVisibility: true,
  trackVisibility: true,
  thickness: 6,
  radius: Radius.circular(3),
  minThumbLength: 40,
  fadeDuration: Duration(milliseconds: 300),
  timeToFade: Duration(seconds: 2),
  child: ListView.builder(controller: _controller, itemCount: 50, itemBuilder: (_, i) => ListTile(title: Text('$i'))),
)
```

---

## StatefulBuilder

Adds `setState` to a small, isolated part of a build method — avoids extracting a full widget.

```dart
// Useful inside showDialog, showModalBottomSheet, etc.
showDialog(
  context: context,
  builder: (context) {
    return StatefulBuilder(
      builder: (context, setDialogState) {
        return AlertDialog(
          title: Text('Filters'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              CheckboxListTile(
                title: Text('Show archived'),
                value: _showArchived,
                onChanged: (v) => setDialogState(() => _showArchived = v!),
                // ↑ setDialogState triggers rebuild of dialog only
              ),
              CheckboxListTile(
                title: Text('Show deleted'),
                value: _showDeleted,
                onChanged: (v) => setDialogState(() => _showDeleted = v!),
              ),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context), child: Text('Apply')),
          ],
        );
      },
    );
  },
)
```

---

## OrientationBuilder

Rebuilds when device orientation changes.

```dart
OrientationBuilder(
  builder: (context, orientation) {
    if (orientation == Orientation.landscape) {
      return Row(
        children: [
          Expanded(flex: 2, child: MediaPlayer()),
          Expanded(child: MediaDetails()),
        ],
      );
    }
    return Column(
      children: [
        AspectRatio(aspectRatio: 16/9, child: MediaPlayer()),
        MediaDetails(),
      ],
    );
  },
)
```

---

## Builder

Provides a new `BuildContext` that is a descendant of a given widget, enabling access to things like `Scaffold`.

```dart
// Common use: access Scaffold from within the same widget that creates it
Scaffold(
  body: Builder(
    builder: (context) {   // this context is a child of Scaffold
      return ElevatedButton(
        onPressed: () {
          // Works because context is now inside the Scaffold
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Hello!')),
          );
        },
        child: Text('Show SnackBar'),
      );
    },
  ),
)

// Another use: access Theme/Provider where context doesn't have it yet
Builder(
  builder: (context) {
    final theme = Theme.of(context);  // context is below the MaterialApp
    return Text('Color: ${theme.colorScheme.primary}');
  },
)
```

---

## PhysicalModel & Material

### Material — required ancestor for ripples, elevation, ink effects
```dart
Material(
  type: MaterialType.card,        // canvas, card, circle, button, transparency
  elevation: 4,
  color: Colors.white,
  shadowColor: Colors.black26,
  borderRadius: BorderRadius.circular(12),
  clipBehavior: Clip.antiAlias,
  animationDuration: kThemeChangeDuration,
  child: InkWell(
    onTap: () {},
    splashColor: Colors.blue.withOpacity(0.2),
    child: Padding(padding: EdgeInsets.all(16), child: Text('Tappable')),
  ),
)
```

### PhysicalModel — adds elevation with shadow
```dart
PhysicalModel(
  elevation: 8,
  color: Colors.white,
  shadowColor: Colors.black,
  borderRadius: BorderRadius.circular(16),
  clipBehavior: Clip.antiAlias,
  child: Container(width: 200, height: 100, child: Text('Elevated')),
)
```

---

## DecoratedBox & DecoratedBoxTransition

```dart
// DecoratedBox (lighter alternative to Container for just decoration)
DecoratedBox(
  decoration: BoxDecoration(
    gradient: LinearGradient(colors: [Colors.blue, Colors.purple]),
    borderRadius: BorderRadius.circular(12),
  ),
  child: Padding(padding: EdgeInsets.all(16), child: Text('Gradient Box')),
)

// DecoratedBoxTransition — animates decoration changes
DecoratedBoxTransition(
  decoration: DecorationTween(
    begin: BoxDecoration(color: Colors.blue, borderRadius: BorderRadius.circular(0)),
    end: BoxDecoration(color: Colors.purple, borderRadius: BorderRadius.circular(24)),
  ).animate(_controller),
  child: SizedBox(width: 150, height: 60, child: Center(child: Text('Animated'))),
)
```

---

## Placeholder & ErrorWidget

```dart
// Placeholder — grey box with an X, useful during development
Placeholder(
  color: Colors.grey,
  strokeWidth: 2,
  fallbackWidth: 100,
  fallbackHeight: 100,
  child: null,
)

// ErrorWidget — shown when a widget throws during build
// Customize globally:
void main() {
  ErrorWidget.builder = (FlutterErrorDetails details) {
    return Container(
      color: Colors.red[50],
      child: Padding(
        padding: EdgeInsets.all(8),
        child: Text(
          'UI Error: ${details.exception}',
          style: TextStyle(color: Colors.red, fontSize: 12),
        ),
      ),
    );
  };
  runApp(MyApp());
}
```

---

## Banner

Displays a diagonal banner message over a widget (like the DEBUG banner).

```dart
Banner(
  message: 'BETA',
  location: BannerLocation.topEnd,       // topStart, topEnd, bottomStart, bottomEnd
  color: Colors.orange,
  textStyle: TextStyle(color: Colors.white, fontSize: 10, fontWeight: FontWeight.bold),
  textDirection: TextDirection.ltr,
  child: Card(child: ProductCard()),
)

// CheckedModeBanner (Debug banner in MaterialApp)
MaterialApp(
  debugShowCheckedModeBanner: false,  // hide the DEBUG banner
)
```

---

## AnnotatedRegion

Changes system UI overlays (status bar color, brightness) for specific parts of the screen.

```dart
AnnotatedRegion<SystemUiOverlayStyle>(
  value: SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.dark,     // dark icons on light bg
    statusBarBrightness: Brightness.light,        // iOS
    systemNavigationBarColor: Colors.white,
    systemNavigationBarIconBrightness: Brightness.dark,
    systemNavigationBarDividerColor: Colors.transparent,
  ),
  child: Scaffold(
    extendBodyBehindAppBar: true,
    appBar: AppBar(backgroundColor: Colors.transparent, elevation: 0),
    body: Stack(
      children: [
        Image.asset('background.jpg', fit: BoxFit.cover, width: double.infinity),
        // content...
      ],
    ),
  ),
)

// Or set globally in initState
SystemChrome.setSystemUIOverlayStyle(SystemUiOverlayStyle.dark)
SystemChrome.setSystemUIOverlayStyle(SystemUiOverlayStyle.light)

// Lock orientation
SystemChrome.setPreferredOrientations([
  DeviceOrientation.portraitUp,
  DeviceOrientation.portraitDown,
])
```

---

## Cupertino Widgets

iOS-style widgets from `package:flutter/cupertino.dart`.

### CupertinoApp & CupertinoPageScaffold
```dart
import 'package:flutter/cupertino.dart';

CupertinoApp(
  theme: CupertinoThemeData(
    primaryColor: CupertinoColors.activeBlue,
    brightness: Brightness.light,
    textTheme: CupertinoTextThemeData(
      primaryColor: CupertinoColors.activeBlue,
    ),
  ),
  home: CupertinoPageScaffold(
    navigationBar: CupertinoNavigationBar(
      middle: Text('Home'),
      trailing: CupertinoButton(
        padding: EdgeInsets.zero,
        onPressed: () {},
        child: Icon(CupertinoIcons.add),
      ),
    ),
    child: SafeArea(child: MyContent()),
  ),
)
```

### CupertinoNavigationBar
```dart
CupertinoNavigationBar(
  leading: CupertinoButton(
    padding: EdgeInsets.zero,
    onPressed: () => Navigator.pop(context),
    child: Row(mainAxisSize: MainAxisSize.min, children: [
      Icon(CupertinoIcons.back, size: 18),
      Text('Back'),
    ]),
  ),
  middle: Text('Detail'),
  trailing: CupertinoButton(
    padding: EdgeInsets.zero,
    onPressed: _share,
    child: Icon(CupertinoIcons.share),
  ),
  backgroundColor: CupertinoColors.systemBackground,
  border: Border(bottom: BorderSide(color: CupertinoColors.separator, width: 0.5)),
)

// Large title nav bar (iOS 11+ style)
CupertinoSliverNavigationBar(
  largeTitle: Text('Inbox'),
  trailing: CupertinoButton(
    padding: EdgeInsets.zero,
    child: Icon(CupertinoIcons.compose),
    onPressed: () {},
  ),
)
```

### CupertinoTabScaffold
```dart
CupertinoTabScaffold(
  tabBar: CupertinoTabBar(
    activeColor: CupertinoColors.activeBlue,
    inactiveColor: CupertinoColors.inactiveGray,
    items: [
      BottomNavigationBarItem(icon: Icon(CupertinoIcons.home), label: 'Home'),
      BottomNavigationBarItem(icon: Icon(CupertinoIcons.search), label: 'Search'),
      BottomNavigationBarItem(icon: Icon(CupertinoIcons.person), label: 'Profile'),
    ],
  ),
  tabBuilder: (context, index) {
    switch (index) {
      case 0: return CupertinoTabView(builder: (_) => HomeScreen());
      case 1: return CupertinoTabView(builder: (_) => SearchScreen());
      default: return CupertinoTabView(builder: (_) => ProfileScreen());
    }
  },
)
```

### CupertinoTextField
```dart
CupertinoTextField(
  controller: _controller,
  placeholder: 'Search',
  prefix: Padding(
    padding: EdgeInsets.only(left: 8),
    child: Icon(CupertinoIcons.search, color: CupertinoColors.systemGrey),
  ),
  suffix: CupertinoButton(
    padding: EdgeInsets.zero,
    onPressed: _controller.clear,
    child: Icon(CupertinoIcons.xmark_circle_fill, color: CupertinoColors.systemGrey),
  ),
  clearButtonMode: OverlayVisibilityMode.editing,  // show clear button while editing
  padding: EdgeInsets.symmetric(horizontal: 12, vertical: 10),
  decoration: BoxDecoration(
    color: CupertinoColors.systemGrey6,
    borderRadius: BorderRadius.circular(10),
  ),
  keyboardType: TextInputType.text,
  textInputAction: TextInputAction.search,
  onSubmitted: (value) => _search(value),
)
```

### CupertinoSwitch
```dart
CupertinoSwitch(
  value: _isEnabled,
  activeColor: CupertinoColors.activeGreen,
  trackColor: CupertinoColors.systemGrey4,
  thumbColor: CupertinoColors.white,
  onChanged: (value) => setState(() => _isEnabled = value),
)
```

### CupertinoSlider
```dart
CupertinoSlider(
  value: _value,
  min: 0.0,
  max: 100.0,
  divisions: 10,
  activeColor: CupertinoColors.activeBlue,
  thumbColor: CupertinoColors.white,
  onChanged: (v) => setState(() => _value = v),
)
```

### CupertinoPicker
```dart
SizedBox(
  height: 200,
  child: CupertinoPicker(
    itemExtent: 40,
    scrollController: FixedExtentScrollController(initialItem: _selectedIndex),
    onSelectedItemChanged: (index) => setState(() => _selectedIndex = index),
    looping: false,
    magnification: 1.2,
    squeeze: 1.45,
    useMagnifier: true,
    children: cities.map((city) => Center(child: Text(city))).toList(),
  ),
)
```

### CupertinoDatePicker
```dart
SizedBox(
  height: 250,
  child: CupertinoDatePicker(
    mode: CupertinoDatePickerMode.date,     // date, time, dateAndTime
    initialDateTime: DateTime.now(),
    minimumDate: DateTime(2000),
    maximumDate: DateTime(2100),
    minimumYear: 2000,
    maximumYear: 2100,
    use24hFormat: false,
    onDateTimeChanged: (date) => setState(() => _selectedDate = date),
  ),
)

// In a bottom sheet
CupertinoModalPopup:
showCupertinoModalPopup(
  context: context,
  builder: (context) => Container(
    height: 300,
    color: CupertinoColors.systemBackground,
    child: Column(
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            CupertinoButton(onPressed: () => Navigator.pop(context), child: Text('Cancel')),
            CupertinoButton(onPressed: () { _applyDate(); Navigator.pop(context); }, child: Text('Done')),
          ],
        ),
        Expanded(child: CupertinoDatePicker(onDateTimeChanged: (d) => _tempDate = d, initialDateTime: _selectedDate)),
      ],
    ),
  ),
)
```

### CupertinoActionSheet
```dart
showCupertinoModalPopup(
  context: context,
  builder: (context) => CupertinoActionSheet(
    title: Text('Choose Photo'),
    message: Text('Select how you want to add a photo'),
    actions: [
      CupertinoActionSheetAction(
        onPressed: () { Navigator.pop(context); _openCamera(); },
        child: Text('Take Photo'),
      ),
      CupertinoActionSheetAction(
        onPressed: () { Navigator.pop(context); _openGallery(); },
        child: Text('Choose from Library'),
      ),
      CupertinoActionSheetAction(
        isDestructiveAction: true,
        onPressed: () { Navigator.pop(context); _removePhoto(); },
        child: Text('Remove Photo'),
      ),
    ],
    cancelButton: CupertinoActionSheetAction(
      onPressed: () => Navigator.pop(context),
      child: Text('Cancel'),
    ),
  ),
)
```

### CupertinoAlertDialog
```dart
showCupertinoDialog(
  context: context,
  barrierDismissible: false,
  builder: (context) => CupertinoAlertDialog(
    title: Text('Delete Item'),
    content: Text('This action cannot be undone.'),
    actions: [
      CupertinoDialogAction(
        onPressed: () => Navigator.pop(context, false),
        child: Text('Cancel'),
      ),
      CupertinoDialogAction(
        isDestructiveAction: true,
        onPressed: () => Navigator.pop(context, true),
        child: Text('Delete'),
      ),
    ],
  ),
)
```

### CupertinoContextMenu
```dart
CupertinoContextMenu(
  actions: [
    CupertinoContextMenuAction(
      trailingIcon: CupertinoIcons.heart,
      child: Text('Like'),
      onPressed: () { Navigator.pop(context); _like(); },
    ),
    CupertinoContextMenuAction(
      trailingIcon: CupertinoIcons.share,
      child: Text('Share'),
      onPressed: () { Navigator.pop(context); _share(); },
    ),
    CupertinoContextMenuAction(
      trailingIcon: CupertinoIcons.delete,
      isDestructiveAction: true,
      child: Text('Delete'),
      onPressed: () { Navigator.pop(context); _delete(); },
    ),
  ],
  child: ProductCard(),
)
```

### CupertinoSegmentedControl
```dart
CupertinoSegmentedControl<int>(
  groupValue: _selectedSegment,
  onValueChanged: (value) => setState(() => _selectedSegment = value),
  children: {
    0: Padding(padding: EdgeInsets.all(8), child: Text('List')),
    1: Padding(padding: EdgeInsets.all(8), child: Text('Grid')),
    2: Padding(padding: EdgeInsets.all(8), child: Text('Map')),
  },
  selectedColor: CupertinoColors.activeBlue,
  unselectedColor: CupertinoColors.white,
  borderColor: CupertinoColors.activeBlue,
)
```

### Platform-adaptive widgets
```dart
// Adaptive switch — Material on Android, Cupertino on iOS
Switch.adaptive(
  value: _value,
  onChanged: (v) => setState(() => _value = v),
)

// Adaptive checkbox
Checkbox.adaptive(value: _checked, onChanged: (v) => setState(() => _checked = v!))

// Adaptive slider
Slider.adaptive(value: _val, onChanged: (v) => setState(() => _val = v))

// Adaptive dialog
import 'dart:io';
Platform.isIOS
    ? showCupertinoDialog(context: context, builder: (_) => CupertinoAlertDialog(...))
    : showDialog(context: context, builder: (_) => AlertDialog(...));
```

---

*Last updated: Flutter 3.x / Dart 3.x — Material 3 + Cupertino*
