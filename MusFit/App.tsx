import React from 'react';
import {StyleSheet, Text, View} from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { SafeAreaView } from 'react-native-safe-area-context';
import HomePage from './src/screens/HomePage';
import ProfilePage from './src/screens/ProfilePage';
import ShopPage from './src/screens/ShopPage';
import SchedulePage from './src/screens/SchedulePage';
import CustomTabBar from './src/components/CustomTabBar';

const Tab = createBottomTabNavigator();

function App(): React.JSX.Element {
  return (
    <SafeAreaView style={{ flex: 1 }}>
      <NavigationContainer>
        <Tab.Navigator tabBar={(prop) => <CustomTabBar {...prop} />}>
          <Tab.Screen 
            name="Home" 
            component={HomePage} 
            options={{ title: 'Event Booking'}}
          />
          <Tab.Screen 
            name="Shop" 
            component={ShopPage} 
            options={{ title: 'Shop For Events'}}
          />
            <Tab.Screen 
            name="Schedule" 
            component={SchedulePage} 
            options={{ title: 'My Schedule'}}
          />
            <Tab.Screen 
            name="Profile" 
            component={ProfilePage} 
            options={{ title: 'My Profile'}}
          />
        </Tab.Navigator>
      </NavigationContainer>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#C0C0C0'
  },
});

export default App;
