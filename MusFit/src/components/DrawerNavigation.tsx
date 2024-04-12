import React from 'react';
import { createDrawerNavigator, DrawerNavigationProp } from '@react-navigation/drawer';
import { NavigationContainer, useNavigation } from '@react-navigation/native';
import { TouchableOpacity, StyleSheet, Text, View } from 'react-native';
import Ionicons from 'react-native-vector-icons/Ionicons';
import HomePage from '../screens/HomePage';
import ProfilePage from '../screens/ProfilePage';

const MyDrawer: React.FC = () => {
  return (
    <Text></Text>
  );
};

const styles = StyleSheet.create({
  menuButton: {
    marginLeft: 10,
  },
});

export default MyDrawer;
