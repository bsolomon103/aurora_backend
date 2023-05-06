dict = {'model': None, 'device': None}

processes = ['appointment']
'''
 _ingredients = ModelIngredients(1).build()  
        for k in self.keys:
            if k not in  ('model', 'device'):
                request.session[k] = _ingredients[k]
            model = _ingredients['model']
            device = _ingredients['device']

            
        serializer = self.serializer_class(data=request.data)
            
        if serializer.is_valid():
            msg = serializer.data['msg']
            # route process requests here if msg - yes
            # clear process here if aborted or finished
            # Only ever 1 process at a time per request.
            if msg.lower() == 'yes':
                print(request.session.session_key)
                print(request.session.get_expiry_date())
            try: 
                response = get_response(msg, 
                                        model, 
                                        request.session['all_words'], 
                                        request.session['tags'],
                                        request.session['intents'],
                                        device
                                        )
                print(response)
                status_code = 200 
                if response['process'] is None:
                    return Response(response['response'], status=status_code)
                else:
                    print(response['process'])
                    request.session['process'] = response['process']
                return Response(response['response'], status=status_code)
                
            
            except Exception as e:
                    # Error check for keys
                    #[print(True) for k in self.keys if k not in request.session]
                    print(e)
                    response = 'wft'
        
                    print('Error')
                    return Response(response, status=200)
        else:
            response = 'Error Bro'
            print(response)
            status_code = 500
            Response(response, status = status_code)
'''









