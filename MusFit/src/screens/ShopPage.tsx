import React from 'react';
import {StyleSheet, Text, View} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

function ShopPage(): React.JSX.Element {
    return (
        <SafeAreaView>
          <Text>Shop Page</Text>
        </SafeAreaView>
    );
  }
  
  const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: '#C0C0C0'
    },
   
  });
  
  export default ShopPage;