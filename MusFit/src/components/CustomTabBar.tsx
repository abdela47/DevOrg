import React from 'react';
import { View, Image, TouchableOpacity, StyleSheet } from 'react-native';
import { BottomTabBarProps } from '@react-navigation/bottom-tabs';

const CustomTabBar: React.FC<BottomTabBarProps> = ({ state, descriptors, navigation }) => {
  const iconMap: { [key: string]: any } = {
    Home: require('../assets/icons/home.png'),
    Profile: require('../assets/icons/user.png'),
    Shop: require('../assets/icons/shopping-cart.png'),
    Schedule: require('../assets/icons/calendar.png')
  };

  return (
    <View style={styles.tabContainer}>
      {state.routes.map((route, index) => {
        const isFocused = state.index === index;
        const iconSource = iconMap[route.name] || require('../assets/icons/home.png');

        const onPress = () => {
          const event = navigation.emit({
            type: 'tabPress',
            target: route.key,
            canPreventDefault: true,
          });

          if (!isFocused && !event.defaultPrevented) {
            navigation.navigate(route.name);
          }
        };

        const onLongPress = () => {
          navigation.emit({
            type: 'tabLongPress',
            target: route.key,
          });
        };

        return (
          <TouchableOpacity
            key={index}
            onPress={onPress}
            onLongPress={onLongPress}
            style={[styles.tab, { opacity: isFocused ? 1 : 0.5 }]} // Focused tabs are fully opaque
          >
            <Image
              source={iconSource}
              style={{ width: 30, height: 30 }}
              resizeMode="contain"
            />
          </TouchableOpacity>
        );
      })}
    </View>
  );
};

const styles = StyleSheet.create({
  tabContainer: {
    flexDirection: 'row',
    height: 50,
    backgroundColor: '#f7f7f7',
    elevation: 2,
    shadowOpacity: 0.1,
    alignItems: 'center',
    justifyContent: 'space-around',
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
});

export default CustomTabBar;
